# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:48:12.443977 |
| Actions | 149 |
| Duration | 498.1 s |
| Cost | $0.3963 |

## Confirmed bugs

### Blue door opened without blue key

Invariant `blue_needs_key`: The blue door stays closed until the blue key is picked up.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to BlueDoor at 3500,0 and interacted; state shows BlueDoor open while BlueKey still present, violating blue\_needs\_key

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

![Before](shots/t004_reset.png)

![After](shots/t006.png)

### Red door did not open with red key

Invariant `red_opens_with_key`: With the red key, interacting with the red door opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up RedKey then interacted at RedDoor within range yet state shows RedDoor closed, violating opens\-with\-key

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
9. Let the game run for 1.0 s

![Before](shots/t008_reset.png)

![After](shots/t010.png)

### Gem bundle only gave 1

Invariant `gem_worth_three`: A gem bundle adds 3 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to GemBundle at 2000,300, it went missing but InventoryCount is 1 instead of 3, violating gem worth 3\.

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s

![Before](shots/t014_reset.png)

![After](shots/t016.png)

## Rejected hypotheses

None.
