# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T13:46:19.731980 |
| Actions | 125 |
| Duration | 423.3 s |
| Cost | $0.2833 |

## Confirmed bugs

### BlueDoor opens without BlueKey

Invariant `blue_door_needs_blue_key`: BlueDoor must not open while BlueKey is still present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: At \(3455,0\) interacted near BlueDoor with BlueKey still present and BlueDoor transitioned to open, violating needs\-key condition

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Press Interact
9. Let the game run for 1.0 s

![Before](shots/t009_reset.png)

![After](shots/t011.png)

### GemBundle only adds 1 instead of 3

Invariant `gem_bundle_worth_three`: GemBundle adds 3 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected Coin \(\+1\) then GemBundle; inventory went 0\-\>1\-\>2, so GemBundle delta was 1 not 3, violating gem\_bundle\_worth\_three

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2000, 300)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s

![Before](shots/t023_reset.png)

![After](shots/t026.png)

## Rejected hypotheses

None.
