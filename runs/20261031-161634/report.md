# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model |  |
| Started | 2026-10-31T16:16:34.332212 |
| Actions | 20 |
| Duration | 88.5 s |
| Cost | $0.0 |

## Confirmed bugs

### gold\_worth\_five broken \(scripted check\)

Invariant `gold_worth_five`: Collecting the gold coin adds exactly 5 to the inventory.

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

### gold\_walkover broken \(scripted check\)

Invariant `gold_walkover`: The gold coin is collected only by walking over it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object ExitDoor episode broke gold\_walkover\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 6.833333333333333 s
3. Press Interact

![Before](shots/baseline_000_before.png)

![After](shots/baseline_000_after.png)

### side\_door\_opens broken \(scripted check\)

Invariant `side_door_opens`: Interacting next to the side door opens it with or without anything in their pockets.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object SideDoor episode broke side\_door\_opens\.

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
