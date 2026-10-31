# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T13:39:05.209127 |
| Actions | 136 |
| Duration | 434.4 s |
| Cost | $0.2631 |

## Confirmed bugs

### GemBundle gives 1 instead of 3

Invariant `gem_bundle_worth_three`: GemBundle adds exactly 3 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to GemBundle location and it disappeared but InventoryCount only increased to 1; expected \+3\. Auto\-check incorrectly reports holds\.

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s

![Before](shots/t008_reset.png)

![After](shots/t010.png)

### Blue door opened without collecting BlueKey

Invariant `blue_door_needs_blue_key`: Blue door cannot open while BlueKey is still present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Interacted with BlueDoor at 3500,0 without picking up BlueKey; State shows BlueDoor\=open while BlueKey\=present, breaking the requires\-key rule\.

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

![Before](shots/t010_reset.png)

![After](shots/t012.png)

### Red door does not open with RedKey

Invariant `red_door_opens_with_red_key`: Interacting with RedDoor while carrying RedKey must open it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected RedKey \(state missing, within 50cm of RedDoor at 2200,\-700\) and executed interact, but RedDoor remains closed instead of opening, violating the required open\-on\-interact behavior\.

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

![Before](shots/t012_reset.png)

![After](shots/t014.png)

## Rejected hypotheses

None.
