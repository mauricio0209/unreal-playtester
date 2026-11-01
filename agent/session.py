"""One-command playtest session runner (standard library only).

Usage:
    python3 agent/session.py [--provider meta|baseten] [--model ID]
                             [--turns N] [--minutes M]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TURNS = 40
DEFAULT_MINUTES = 10.0
EXPLORATION_SHARE = 0.6
DUPLICATE_REASON = "duplicate of a confirmed bug"


def _resolve_now(now):
    if now is None:
        return datetime.now()
    if callable(now):
        return now()
    return now


def _rel_to_run_dir(value, run_dir):
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    if os.path.isabs(text):
        try:
            return str(Path(text).relative_to(run_dir))
        except ValueError:
            return os.path.relpath(text, str(run_dir))
    return text


def _jsonable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _invariant_descriptions(spec):
    descriptions = {}
    for invariant in spec.get("invariants", []) or []:
        if isinstance(invariant, dict) and "id" in invariant:
            descriptions[invariant["id"]] = invariant.get("description",
                                                          "") or ""
    return descriptions


def main(argv=None, ue=None, client=None, explorer_mod=None, now=None,
         run_root=None, video_mod=None):
    parser = argparse.ArgumentParser(description="Run a playtest session.")
    parser.add_argument("--provider", default="meta",
                        choices=("meta", "baseten", "script"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default="low",
                        help="reasoning_effort sent to the model ('' to omit)")
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    parser.add_argument("--minutes", type=float, default=DEFAULT_MINUTES)
    parser.add_argument("--level", default="arena",
                        choices=["arena"] + sorted(f.stem for f in (HERE / "levels").glob("*.md")),
                        help="arena: hand-written spec.json; any other level: the model writes "
                             "the checks from levels/<level>.md (PIE must be playing that map)")
    parser.add_argument("--checks", default=None,
                        help="reuse a checks.json from an earlier run instead of asking the model")
    parser.add_argument("--no-video", action="store_true",
                        help="skip replay videos for confirmed bugs")
    args = parser.parse_args(argv)

    deadline_s = float(args.minutes) * 60.0 * EXPLORATION_SHARE

    start_dt = _resolve_now(now)
    monotonic_start = time.monotonic()

    repo_root = (Path(__file__).resolve().parent.parent
                 if run_root is None else Path(run_root))
    stamp = start_dt.strftime("%Y%m%d-%H%M%S")
    (repo_root / "runs").mkdir(parents=True, exist_ok=True)
    suffix = 1
    while True:  # mkdir is atomic: two sessions starting in the same second get two dirs
        run_dir = repo_root / "runs" / (stamp if suffix == 1 else f"{stamp}-{suffix}")
        try:
            run_dir.mkdir()
            break
        except FileExistsError:
            suffix += 1
    shots_dir = run_dir / "shots"
    shots_dir.mkdir()

    if client is None and args.provider != "script":
        import llm as llm_mod
        client = llm_mod.from_env(args.provider, model=args.model,
                                  reasoning_effort=args.effort or None)
    if ue is None:
        import ue as ue_mod
        ue = ue_mod
    import verifier as verifier_mod
    import report as report_mod
    if explorer_mod is None:
        if args.provider == "script":
            import baseline as explorer_mod
        else:
            import explorer as explorer_mod
    if video_mod is None:
        import replay_video as video_mod

    log_file = (run_dir / "explore.log").open("w", encoding="utf-8")

    def log(line):
        print(line)
        log_file.write(line + "\n")
        log_file.flush()

    if args.level == "arena":
        spec = verifier_mod.load_spec(str(HERE / "spec.json"))
    else:
        import checks as checks_mod
        import oracle
        if hasattr(ue, "HARNESS_PATH"):
            ue.HARNESS_PATH = ue.HARNESS_PATH.replace("Arena", args.level.capitalize())
        if args.checks:
            checks = json.loads(Path(args.checks).read_text(encoding="utf-8"))
            for check in checks:  # the file may have been edited: same trust boundary
                checks_mod.validate(check)
        elif client is None:
            parser.error("--provider script needs --checks: it cannot write checks itself")
        else:
            checks = oracle.write_checks(client, (HERE / "levels" / f"{args.level}.md")
                                         .read_text(encoding="utf-8"), ue.reset(), log=log)
        (run_dir / "checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
        for check in checks:
            log(f"check {check['id']}: {check['description']}")
        spec = oracle.to_spec(checks)

    result = explorer_mod.explore(ue, client, spec, shots_dir,
                                 max_turns=int(args.turns),
                                 deadline_s=deadline_s, log=log)

    hypotheses = result.get("hypotheses", []) or []
    actions = result.get("actions", 0)
    descriptions = _invariant_descriptions(spec)

    confirmed_invariants = set()
    findings = []
    for hypothesis in hypotheses:
        invariant = hypothesis.get("invariant")
        steps = hypothesis.get("steps", [])
        if invariant in confirmed_invariants:
            verdict = {"invariant": invariant, "confirmed": False, "runs": [],
                       "reason": DUPLICATE_REASON}
        else:
            try:
                verdict = verifier_mod.verify(ue, steps, invariant, spec)
            except ValueError as exc:
                verdict = {"invariant": invariant, "confirmed": False,
                           "runs": [], "reason": str(exc)}
            if verdict.get("confirmed"):
                confirmed_invariants.add(invariant)
        findings.append({
            "title": hypothesis.get("title", ""),
            "hypothesis": hypothesis.get("hypothesis", ""),
            "invariant": invariant,
            "invariant_description": descriptions.get(invariant, ""),
            "steps": steps,
            "verdict": verdict,
            "before": _rel_to_run_dir(hypothesis.get("before"), run_dir),
            "after": _rel_to_run_dir(hypothesis.get("after"), run_dir),
            "video_gif": None,
            "video_mp4": None,
        })

    if not args.no_video:
        videos_dir = run_dir / "videos"
        bug_index = 0
        for finding in findings:
            if not (finding.get("verdict") or {}).get("confirmed"):
                continue
            bug_index += 1
            name = f"bug{bug_index}"
            try:
                result = video_mod.record(
                    ue, finding.get("steps", []), videos_dir, name)
            except Exception as exc:
                log(f"video recording failed for {name}: {exc}")
                finding["video_gif"] = None
                finding["video_mp4"] = None
                continue
            finding["video_gif"] = _rel_to_run_dir(result.get("gif"),
                                                   run_dir)
            finding["video_mp4"] = _rel_to_run_dir(result.get("mp4"),
                                                   run_dir)

    log_file.close()

    duration_s = time.monotonic() - monotonic_start
    model_name = getattr(client, "model", None) or args.model or ""
    try:
        cost = round(float(getattr(client, "cost_usd", 0.0)), 4)
    except (TypeError, ValueError):
        cost = 0.0
    session_info = {"started": start_dt.isoformat(), "model": model_name,
                    "actions": actions, "cost_usd": cost,
                    "duration_s": round(duration_s, 1), "level": args.level}

    report_path = report_mod.write_report(run_dir, session_info, findings)
    session_doc = {"session": session_info, "findings": findings,
                   "hypotheses": [_jsonable(h) for h in hypotheses]}
    (run_dir / "session.json").write_text(json.dumps(session_doc, indent=2),
                                          encoding="utf-8")
    import report_html
    report_html.write_html(run_dir, args.level)

    n_confirmed = sum(1 for f in findings
                      if (f.get("verdict") or {}).get("confirmed"))
    n_rejected = len(findings) - n_confirmed
    print(str(report_path))
    print(f"{n_confirmed} confirmed bugs, {n_rejected} rejected hypotheses "
          f"(actions={actions}, cost=${cost}, duration={duration_s:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
