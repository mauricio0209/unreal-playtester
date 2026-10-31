"""Grade Vault runs against the seeded bugs by replaying every confirmed finding.

Usage: python3 scripts/grade_vault.py runs/<list>.txt   (PIE must be playing the Vault)

This is the answer key: it lives outside agent/ and the agent never sees it. A confirmed
finding counts as a seeded bug only if replaying its repro shows that bug AND its model-written
check reads that bug's object; anything else is a false positive. Keyword grading misfired
twice (one check covering three doors; "RedKey vanished" read as the red door bug).
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import checks  # noqa: E402
import ue  # noqa: E402
import verifier  # noqa: E402

V = lambda path: {"var": path}  # noqa: E731
P = lambda path: {"prev": path}  # noqa: E731
SEEDED = {  # bug -> (object the finding's check must read, ground-truth violation)
    "blue_door_opens_without_key": ("BlueDoor", {"ever": {"and": [
        {"==": [V("ActorStates.BlueDoor"), "open"]}, {"==": [V("ActorStates.BlueKey"), "present"]}]}}),
    "red_door_wrong_key": ("RedDoor", {"or": [
        {"ever": {"and": [{"==": [V("ActorStates.RedDoor"), "open"]},
                          {"==": [V("ActorStates.RedKey"), "present"]}]}},
        {"after": [{"and": [{"did": "interact"}, {"==": [V("ActorStates.RedKey"), None]},
                            {"<": [{"dist": ["PlayerLocation", "ActorLocations.RedDoor"]}, 150]}]},
                   {"==": [V("ActorStates.RedDoor"), "closed"]}]}]}),
    "gem_bundle_adds_one": ("GemBundle", {"ever": {"and": [
        {"==": [P("ActorStates.GemBundle"), "present"]}, {"==": [V("ActorStates.GemBundle"), None]},
        {"!=": [{"-": [V("InventoryCount"), P("InventoryCount")]}, 3]}]}}),
}


def grade_run(run_dir):
    run_dir = Path(run_dir)
    session = json.loads((run_dir / "session.json").read_text())
    model_checks = {c["id"]: c for c in json.loads((run_dir / "checks.json").read_text())}
    found, false_positives = set(), []
    for f in session["findings"]:
        if not f["verdict"]["confirmed"]:
            continue
        trace = verifier.run_steps(ue, f["steps"])
        reads = json.dumps(model_checks[f["invariant"]]["violation"])
        hits = [bug for bug, (obj, expr) in SEEDED.items()
                if obj in reads and checks.evaluate(trace, expr)]
        found.update(hits)
        if not hits:
            false_positives.append(f"{f['invariant']} ({f.get('title', '')})")
    return found, false_positives, session["session"]


def main():
    ue.HARNESS_PATH = os.environ.get(
        "UE_HARNESS_PATH", "/Game/Maps/UEDPIE_0_Vault.Vault:PersistentLevel.BP_TestHarness_C_0")
    totals = {}
    for line in Path(sys.argv[1]).read_text().splitlines():
        if not line.strip():
            continue
        provider, run = line.split()
        found, fps, info = grade_run(ROOT / run)
        t = totals.setdefault(provider, {"n": 0, "real": 0, "all3": 0, "fp": 0, "min": 0.0})
        t["n"] += 1
        t["real"] += len(found)
        t["all3"] += len(found) == len(SEEDED)
        t["fp"] += len(fps)
        t["min"] += info["duration_s"] / 60
        print(f"{provider} {run}: {len(found)}/3 {sorted(found)} | false positives {len(fps)} {fps}")
    for provider, t in totals.items():
        print(f"TOTAL {provider} n={t['n']}: mean real {t['real'] / t['n']:.1f}/3, "
              f"all 3 in {t['all3']}/{t['n']}, false positives {t['fp']}, "
              f"mean {t['min'] / t['n']:.1f} min")


if __name__ == "__main__":
    main()
