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
        "Do not write checks for things the document does not state. "
        'Reply with exactly one JSON object {"checks": [...]} and nothing else.'
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


def write_checks(llm, design_text, state, log=print, attempts=3, validate=None) -> list[dict]:
    """Ask the model for checks, retrying rejected ones. See tasks/oracle.md."""
    if validate is None:
        from checks import validate as validate
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
            raw = _extract_json(reply)
        except (ValueError, json.JSONDecodeError) as exc:
            new_valid: list[dict] = []
            rejected = [(None, f"unparseable reply: {exc}")]
            parse_failed = True
        else:
            try:
                new_valid, rejected = _validate_checks(raw, validate)
            except ValueError as exc:
                new_valid = []
                rejected = [(None, str(exc))]
                parse_failed = True
            else:
                parse_failed = False
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
                f"({detail}). Reply with the complete corrected list as exactly "
                'one JSON object {"checks": [...]} and nothing else.'
            )
        elif not rejected:
            feedback = (
                "Your reply contained no checks. Reply with the complete "
                "corrected list as exactly "
                'one JSON object {"checks": [...]} and nothing else.'
            )
        else:
            detail = "; ".join(f"{cid}: {err}" for cid, err in rejected)
            feedback = (
                "Some checks were rejected "
                f"({detail}). Reply with the complete corrected list as exactly "
                'one JSON object {"checks": [...]} and nothing else.'
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
