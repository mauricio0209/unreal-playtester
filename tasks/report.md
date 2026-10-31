# Task: session report (`agent/report.py`)

Create `agent/report.py` and `agent/test_report.py`. Python 3.14, standard library only. Do not
modify any other file. Run `python3 agent/test_report.py` and make sure it passes before
finishing.

## Context

An LLM explorer plays a game and files bug hypotheses. A deterministic verifier replays each
one 3 times. This module writes the human-readable report of a session. The report is the
product judges and game developers read, and success criterion 4 is: "every report can be
reproduced by a human from its steps alone".

## Input

```python
finding = {
    "title": "Door does not open when interacting next to it",   # from the explorer
    "hypothesis": "free text the explorer wrote",
    "invariant": "door_opens",                                    # spec invariant id
    "invariant_description": "Doors open when the player interacts within 150 cm.",
    "steps": [{"action": "move_to", "x": 3350, "y": 0}, {"action": "step", "seconds": 3.0},
              {"action": "interact"}, {"action": "step", "seconds": 1.0}],
    "verdict": {"invariant": "door_opens", "confirmed": True, "runs": [True, True, True],
                "reason": "bug reproduced in all 3 runs"},
    "before": "shots/f1_before.png",   # paths relative to run_dir, may be None
    "after": "shots/f1_after.png",
}
session = {"started": "2026-11-02T10:00:00", "model": "muse-spark-1.3", "actions": 57,
           "cost_usd": 0.42, "duration_s": 380.5}
```

Allowed actions in steps: `move_to` (x, y), `look_at` (x, y, z), `jump`, `interact`,
`step` (seconds).

## API

```python
def describe_step(step: dict) -> str
    # One plain-English imperative line a human can follow in the editor, e.g.
    # "Walk to (3350, 0)", "Look at (100, 0, 50)", "Jump", "Press Interact",
    # "Let the game run for 3.0 s". Coordinates rounded to whole centimetres.

def write_report(run_dir, session: dict, findings: list[dict]) -> Path
    # Write run_dir/report.md and return its path.
```

## Report content (Markdown)

1. Title and a one-line summary: N confirmed bugs, M rejected hypotheses.
2. Session table: model, start time, number of actions, duration, cost.
3. "Confirmed bugs" section first, then "Rejected hypotheses". Each finding gets: its title as
   a heading, the invariant id and description, the verdict with the per-run results
   (e.g. "3/3 runs reproduced"), the numbered repro steps from `describe_step` preceded by
   "Start from a fresh level load.", and the before/after screenshots as Markdown images
   when present.
4. Escape Markdown-significant characters in the explorer's free text (title, hypothesis)
   so model output cannot break the layout or inject links/images. This is a trust boundary.

## Tests

Cover: `describe_step` for every action; summary counts; confirmed findings listed before
rejected ones; missing screenshots produce no image line; explorer text containing
`![x](http://evil)` and `#` headings is escaped; the file is written under `run_dir`.
