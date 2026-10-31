"""Grade model-written-check runs against the seeded bugs by replaying every confirmed finding.

Usage: python3 scripts/grade_runs.py <level> runs/<list>.txt   (PIE must be playing that map)

This is the answer key: it lives outside agent/ and the agent never sees it. A confirmed
finding counts as a seeded bug only if replaying its repro shows that bug AND its model-written
check reads one of that bug's objects; anything else is a false positive. Keyword grading misfired
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
NOT_IN_PIT = {"or": [{"<": [V("LastFloorLocation.X"), 2300]}, {">": [V("LastFloorLocation.X"), 2700]},
                     {"<": [V("LastFloorLocation.Y"), 300]}, {">": [V("LastFloorLocation.Y"), 700]}]}
ANSWER_KEYS = {}  # level -> bug -> (objects the check must read one of, ground-truth violation)
ANSWER_KEYS["vault"] = {
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
ANSWER_KEYS["armory"] = {
    "side_door_locked": ("SideDoor", {"after": [
        {"and": [{"did": "interact"},
                 {"<": [{"dist": ["PlayerLocation", "ActorLocations.SideDoor"]}, 150]}]},
        {"==": [V("ActorStates.SideDoor"), "closed"]}]}),
    "gold_coin_adds_one": ("GoldCoin", {"ever": {"and": [
        {"==": [P("ActorStates.GoldCoin"), "present"]}, {"==": [V("ActorStates.GoldCoin"), None]},
        {"!=": [{"-": [V("InventoryCount"), P("InventoryCount")]}, 5]}]}}),
    "floor_hole": (("PawnAlive", "LastZ", "KillZ", "PlayerLocation.Z", "LastFloorLocation"),
                   {"ever": {"and": [{"or": [{"==": [V("PawnAlive"), False]},
                                             {"<": [V("LastZ"), -200]}]}, NOT_IN_PIT]}}),
}


def grade_run(run_dir, seeded):
    run_dir = Path(run_dir)
    session = json.loads((run_dir / "session.json").read_text())
    model_checks = {c["id"]: c for c in json.loads((run_dir / "checks.json").read_text())}
    found, false_positives = set(), []
    for f in session["findings"]:
        if not f["verdict"]["confirmed"]:
            continue
        trace = verifier.run_steps(ue, f["steps"])
        reads = json.dumps(model_checks[f["invariant"]]["violation"])
        hits = [bug for bug, (objs, expr) in seeded.items()
                if any(o in reads for o in ((objs,) if isinstance(objs, str) else objs))
                and checks.evaluate(trace, expr)]
        found.update(hits)
        if not hits:
            false_positives.append(f"{f['invariant']} ({f.get('title', '')})")
    return found, false_positives, session["session"]


def main():
    level, runs_list = sys.argv[1], sys.argv[2]
    seeded = ANSWER_KEYS[level]
    name = level.capitalize()
    ue.HARNESS_PATH = os.environ.get(
        "UE_HARNESS_PATH", f"/Game/Maps/UEDPIE_0_{name}.{name}:PersistentLevel.BP_TestHarness_C_0")
    totals = {}
    for line in Path(runs_list).read_text().splitlines():
        if not line.strip():
            continue
        provider, run = line.split()
        found, fps, info = grade_run(ROOT / run, seeded)
        t = totals.setdefault(provider, {"n": 0, "real": 0, "all3": 0, "fp": 0, "min": 0.0})
        t["n"] += 1
        t["real"] += len(found)
        t["all3"] += len(found) == len(seeded)
        t["fp"] += len(fps)
        t["min"] += info["duration_s"] / 60
        print(f"{provider} {run}: {len(found)}/{len(seeded)} {sorted(found)} | false positives {len(fps)} {fps}")
    for provider, t in totals.items():
        print(f"TOTAL {provider} n={t['n']}: mean real {t['real'] / t['n']:.1f}/{len(seeded)}, "
              f"all 3 in {t['all3']}/{t['n']}, false positives {t['fp']}, "
              f"mean {t['min'] / t['n']:.1f} min")


if __name__ == "__main__":
    main()
