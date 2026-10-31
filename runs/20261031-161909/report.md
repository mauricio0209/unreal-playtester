# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model |  |
| Started | 2026-10-31T16:19:09.749266 |
| Actions | 20 |
| Duration | 66.8 s |
| Cost | $0.0 |

## Confirmed bugs

### gold\_worth\_five broken \(scripted check\)

Invariant `gold_worth_five`: The gold coin adds 5 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object ExitDoor episode broke gold\_worth\_five\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 6.833333333333333 s

![Before](shots/baseline_000_before.png)

![After](shots/baseline_000_after.png)

### side\_door\_opens\_empty broken \(scripted check\)

Invariant `side_door_opens_empty`: Standing next to the side door and interacting with empty pockets opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object SideDoor episode broke side\_door\_opens\_empty\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 2.2133516482134197 s
3. Press Interact
4. Let the game run for 1.0 s

![Before](shots/baseline_002_before.png)

![After](shots/baseline_002_after.png)

## Rejected hypotheses

None.
