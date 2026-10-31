# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T13:31:31.216292 |
| Actions | 139 |
| Duration | 453.8 s |
| Cost | $0.2504 |

## Confirmed bugs

### RedDoor does not open with RedKey

Invariant `red_door_opens_with_red_key`: Interacting with RedDoor up close while carrying RedKey must open it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked RedKey \(now missing/inventory\) and interacted up close at 2156,\-697 near RedDoor 2200,\-700; door remained closed per state and screenshot wall, violating must\-open rule\.

Repro:

Start from a fresh level load.

1. Walk to (1500, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Walk to (2200, -700)
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Look at (2200, -700, 150)
10. Walk to (2200, -700)
11. Let the game run for 1.0 s
12. Look at (2200, -700, 150)
13. Press Interact
14. Let the game run for 1.0 s

![Before](shots/t011_reset.png)

![After](shots/t014.png)

### BlueDoor opened without collecting BlueKey

Invariant `blue_door_needs_blue_key`: BlueDoor must not open while BlueKey is still present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked directly to BlueDoor at 3500,0 and interacted with inventory 0 and BlueKey still present, but state became open, breaking requirement that BlueKey must be collected first\.

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

![Before](shots/t014_reset.png)

![After](shots/t016.png)

### GemBundle adds only 1 instead of 3

Invariant `gem_bundle_worth_three`: GemBundle adds exactly 3 to InventoryCount when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up GemBundle at \~2000,300: Inventory went 0\-\>1 not 0\-\>3, Coin still present, so GemBundle worth incorrect breaking gem\_bundle\_worth\_three

Repro:

Start from a fresh level load.

1. Let the game run for 0.5 s
2. Walk to (2000, 300)
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s

![Before](shots/t020_reset.png)

![After](shots/t023.png)

## Rejected hypotheses

None.
