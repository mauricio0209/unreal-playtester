# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:47:40.884355 |
| Actions | 154 |
| Duration | 426.1 s |
| Cost | $0.3014 |

## Confirmed bugs

### GemBundle gave 1 instead of 3

Invariant `gem_bundle_worth_three`: GemBundle adds 3 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Inventory went from 1 to 2 after collecting GemBundle \(delta 1\) instead of expected delta 3, so invariant fails

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

![Before](shots/t006_reset.png)

![After](shots/t009.png)

### RedDoor did not open when interacting while carrying RedKey

Invariant `red_door_opens_with_key`: Interacting with RedDoor up close while carrying RedKey must open it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player picked up RedKey \(now missing/null\) and interacted within \~44cm of RedDoor at 2200,\-700 but Objects\.RedDoor\.state remained 'closed' and screenshot shows closed wall, violating the requirement that it must open\.

Repro:

Start from a fresh level load.

1. Let the game run for 0.5 s
2. Walk to (1500, 300)
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Walk to (2200, -700)
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t025_reset.png)

![After](shots/t028.png)

## Rejected hypotheses

None.
