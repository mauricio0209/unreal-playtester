"""Sunday checkpoint: the verifier confirms each seeded bug from hand-written repro steps
and rejects the decoy and a harmless walk. Needs PIE running in the Arena level.

Run: python3 agent/check_seeded.py
"""

from pathlib import Path

import ue
import verifier

CASES = [  # (name, invariant, steps, expected confirmed)
    ("floor without collision", "no_fall_out_of_world",
     [{"action": "move_to", "x": 2500, "y": -500}, {"action": "step", "seconds": 8.0}], True),
    ("door trigger misaligned", "door_opens",
     [{"action": "move_to", "x": 3440, "y": 0}, {"action": "step", "seconds": 7.0},
      {"action": "interact"}, {"action": "step", "seconds": 1.0}], True),
    ("pickup not counted", "pickup_counts",
     [{"action": "move_to", "x": 1000, "y": 500}, {"action": "step", "seconds": 3.0}], True),
    ("decoy pit", "no_fall_out_of_world",
     [{"action": "move_to", "x": 2500, "y": 500}, {"action": "step", "seconds": 8.0}], False),
    ("decoy pit from the east", "no_fall_out_of_world",
     [{"action": "move_to", "x": 3200, "y": 500}, {"action": "step", "seconds": 7.0},
      {"action": "move_to", "x": 2300, "y": 500}, {"action": "step", "seconds": 5.0}], False),
    ("harmless walk", "no_fall_out_of_world",
     [{"action": "move_to", "x": 1000, "y": -500}, {"action": "step", "seconds": 3.0}], False),
]


def main():
    spec = verifier.load_spec(Path(__file__).with_name("spec.json"))
    failures = 0
    for name, invariant, steps, expected in CASES:
        v = verifier.verify(ue, steps, invariant, spec)
        ok = v["confirmed"] == expected
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'} {name}: confirmed={v['confirmed']} runs={v['runs']}")
    raise SystemExit(failures)


if __name__ == "__main__":
    main()
