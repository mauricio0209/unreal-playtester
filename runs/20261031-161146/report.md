# Session report

1 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model |  |
| Started | 2026-10-31T16:11:46.579220 |
| Actions | 20 |
| Duration | 55.6 s |
| Cost | $0.0 |

## Confirmed bugs

### gold\_worth\_five broken \(scripted check\)

Invariant `gold_worth_five`: Gold coin adds exactly 5 to inventory.

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

## Rejected hypotheses

None.
