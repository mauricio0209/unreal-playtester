"""Model-written level checks from a design document.

Standard library only.
"""

import json
from pathlib import Path


def _system_prompt() -> str:
    ref = (Path(__file__).resolve().parent / "checks_reference.md").read_text(encoding="utf-8")
    instructions = (
        "Write one check for every rule in the design document that "
        "can be observed in the game state. "
        "Use object names exactly as they appear in the sample state. "
        "A check must be true only when the rule is broken, never during normal play. "
        "Most rules have two sides: what must happen (an action must have its effect) and "
        "what must never happen (the effect without its condition). Write a separate check "
        "for each side, or a broken rule can go unreported. "
        "Do not write checks for things the document does not state. "
        "Reply with one check per line, each line a complete JSON object "
        '{"id": ..., "description": ..., "violation": ...}, and nothing else. '
        "Count your closing brackets: every { and [ must be closed on the same line."
    )
    return ref + "\n\n" + instructions


def _user_message(design_text, state) -> str:
    return (
        "Design document:\n"
        f"{design_text}\n"
        "\nSample state right after a level load:\n"
        f"{json.dumps(state)}"
    )


def _extract_json(reply: str):
    """Parse a reply: one check per line (preferred), or a single {"checks": [...]} object.

    Returns (payload, errors): a malformed line only loses that check and its error is fed
    back, instead of one stray bracket discarding the whole list."""
    lines = [ln.strip().rstrip(",") for ln in reply.splitlines() if ln.strip().startswith("{")]
    if len(lines) > 1 or (lines and '"checks"' not in lines[0]):
        checks, errors = [], []
        for n, line in enumerate(lines, 1):
            try:
                checks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append((f"line {n}", f"invalid JSON ({exc}): {line[:120]}"))
        return {"checks": checks}, errors
    return _extract_object(reply), []


def _extract_object(reply: str):
    start = reply.find("{")
    end = reply.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise ValueError("reply contains no JSON object")
    return json.loads(reply[start:end + 1])


def _validate_checks(raw, validate):
    """Return (valid, rejected) for a parsed reply payload."""
    if not isinstance(raw, dict) or not isinstance(raw.get("checks"), list):
        raise ValueError("reply JSON must be an object with a 'checks' list")
    valid = []
    seen = set()
    rejected = []
    for check in raw["checks"]:
        cid = check.get("id") if isinstance(check, dict) else None
        try:
            validate(check)
        except ValueError as exc:
            rejected.append((cid, str(exc)))
            continue
        if not isinstance(cid, str) or cid in seen:
            if isinstance(cid, str):
                continue  # duplicate id: first occurrence wins
            rejected.append((cid, "check needs a string 'id'"))
            continue
        seen.add(cid)
        valid.append(check)
    return valid, rejected


def _paths(expr):
    """Every state path an expression reads."""
    if isinstance(expr, dict):
        for op, arg in expr.items():
            if op in ("var", "prev", "first"):
                yield arg
            elif op == "dist":
                yield from arg
            else:
                yield from _paths(arg)
    elif isinstance(expr, list):
        for item in expr:
            yield from _paths(item)


def guard(check, state):
    """Reject a valid check that is still likely wrong; the message goes back to the model.

    The verifier only proves a check fires reproducibly, not that it is right, so a check
    reading a misspelled name (always null) or already firing on a fresh level load would
    become a confirmed false positive."""
    import checks

    for path in _paths(check["violation"]):
        if checks._lookup_path(state, path) is None:
            names = ", ".join(sorted((state.get("ActorStates") or {})))
            raise ValueError(f"path {path!r} does not exist in the game state (objects: {names})")
    if checks.evaluate([{"action": None, "state": state}], check["violation"]):
        raise ValueError("it already fires on a fresh level load, before the player does "
                         "anything, so it cannot tell a bug from normal play")


def write_checks(llm, design_text, state, log=print, attempts=3, validate=None) -> list[dict]:
    """Ask the model for checks, retrying rejected ones. See tasks/oracle.md."""
    if validate is None:
        import checks

        def validate(check):
            checks.validate(check)
            guard(check, state)
    system = _system_prompt()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": _user_message(design_text, state)},
    ]
    best: list[dict] = []
    for i in range(attempts):
        log(f"attempt {i + 1}/{attempts}: requesting checks")
        reply = llm.chat(messages, max_tokens=8000)
        messages.append({"role": "assistant", "content": reply})
        try:
            raw, line_errors = _extract_json(reply)
        except (ValueError, json.JSONDecodeError) as exc:
            new_valid: list[dict] = []
            rejected = [(None, f"unparseable reply: {exc}")]
            parse_failed = True
        else:
            try:
                new_valid, rejected = _validate_checks(raw, validate)
                rejected = line_errors + rejected
            except ValueError as exc:
                new_valid = []
                rejected = [(None, str(exc))]
                parse_failed = True
            else:
                parse_failed = False
        for cid, err in rejected:
            log(f"  rejected {cid}: {err}")
        if len(new_valid) >= len(best):
            best = new_valid
        if not parse_failed and not rejected and new_valid:
            return best
        if i + 1 >= attempts:
            break
        if parse_failed:
            detail = "; ".join(f"{cid}: {err}" for cid, err in rejected)
            feedback = (
                "Your reply could not be parsed or had no check list "
                f"({detail}). Reply with the complete corrected list, "
                "one check per line as a complete JSON object, and nothing else."
            )
        elif not rejected:
            feedback = (
                "Your reply contained no checks. Reply with the complete "
                "corrected list, one check per line as a complete JSON object, and nothing else."
            )
        else:
            detail = "; ".join(f"{cid}: {err}" for cid, err in rejected)
            feedback = (
                "Some checks were rejected "
                f"({detail}). Reply with the complete corrected list, "
                "one check per line as a complete JSON object, and nothing else."
            )
        messages.append({"role": "user", "content": feedback})
    if not best:
        raise ValueError("no valid check was obtained after all attempts")
    return best


def to_spec(checks, base=None) -> dict:
    """Return a verifier spec with dsl invariants for the given checks."""
    if base is None:
        base = {}
    spec = {
        "intentional": base.get("intentional", []),
        "invariants": [
            {"id": c["id"], "description": c["description"],
             "predicate": "dsl", "params": {"expr": c["violation"]}}
            for c in checks
        ],
    }
    if "level" in base:
        spec["level"] = base["level"]
    return spec
