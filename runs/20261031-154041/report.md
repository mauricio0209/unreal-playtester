# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:40:41.880625 |
| Actions | 132 |
| Duration | 418.8 s |
| Cost | $0.2632 |

## Confirmed bugs

### Blue door opened without key

Invariant `blue_door_never_open_without_key`: Blue door stays closed until blue key is picked up.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to BlueDoor at \(3500,0\) and interacted without picking up BlueKey; state shows BlueDoor open while BlueKey present and inventory 0, so door opened without key\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Look at (3500, 0, 150)
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t004_reset.png)

![After](shots/t006.png)

### Gem bundle gave 1 instead of 3

Invariant `gem_bundle_worth_three`: Gem bundle adds exactly 3 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to GemBundle at \~2000,300; state shows GemBundle missing and InventoryCount\=1; expected increase of 3 from 0 to 3

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s

![Before](shots/t010_reset.png)

![After](shots/t012.png)

## Rejected hypotheses

None.
