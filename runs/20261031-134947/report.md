# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T13:49:47.558255 |
| Actions | 155 |
| Duration | 527.4 s |
| Cost | $0.3649 |

## Confirmed bugs

### Blue door opened without blue key

Invariant `blue_needs_key`: The blue door stays locked until the blue key is picked up.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: State shows BlueDoor open while BlueKey still present and Inventory 0, so door opened without pickup, breaking blue\_needs\_key\.

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
9. Let the game run for 2.0 s

![Before](shots/t007_reset.png)

![After](shots/t009.png)

### Red door did not open with red key

Invariant `red_opens_with_key`: With the red key, interacting with the red door opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: State shows RedKey missing and player at RedDoor after interact, but RedDoor is still closed, so interacting with key failed to open it\.

Repro:

Start from a fresh level load.

1. Walk to (1500, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Press Interact
9. Let the game run for 2.0 s

![Before](shots/t011_reset.png)

![After](shots/t013.png)

### Gem bundle added 1 instead of 3

Invariant `gem_worth_three`: A gem bundle adds 3 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to GemBundle location, GemBundle went present\-\>missing while InventoryCount went 0\-\>1 \(diff 1 \!\=3\), confirmed by state and missing gem in view

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 2.0 s

![Before](shots/t015_reset.png)

![After](shots/t017.png)

## Rejected hypotheses

None.
