# Session report

4 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model |  |
| Started | 2026-10-31T16:13:49.221960 |
| Actions | 20 |
| Duration | 98.2 s |
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

### gold\_no\_distant\_pickup broken \(scripted check\)

Invariant `gold_no_distant_pickup`: The gold coin is only collected when walked over.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object ExitDoor episode broke gold\_no\_distant\_pickup\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 6.833333333333333 s
3. Press Interact

![Before](shots/baseline_000_before.png)

![After](shots/baseline_000_after.png)

### side\_door\_opens broken \(scripted check\)

Invariant `side_door_opens`: The side door opens when interacted with from nearby.

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

### silver\_no\_distant\_pickup broken \(scripted check\)

Invariant `silver_no_distant_pickup`: The silver coin is only collected when walked over.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object SilverCoin episode broke silver\_no\_distant\_pickup\.

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 2.863389981249825 s

![Before](shots/baseline_003_before.png)

![After](shots/baseline_003_after.png)

## Rejected hypotheses

None.
