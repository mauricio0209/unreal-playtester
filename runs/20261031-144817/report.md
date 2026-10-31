# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T14:48:17.944481 |
| Actions | 151 |
| Duration | 491.8 s |
| Cost | $0.286 |

## Confirmed bugs

### Side door did not open

Invariant `side_opens`: Side door opens when interacting next to it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Interacted within 50cm of SideDoor but state stayed closed and view shows wall

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t000.png)

![After](shots/t002.png)

### Gold coin gave 1 not 5

Invariant `gold_five`: Gold coin adds exactly 5 to inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked over Silver then Gold: inventory 0\-\>2\-\>3, so Gold added 1 instead of 5, confirming gold\_five violation\.

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (1500, 0)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s

![Before](shots/t002_reset.png)

![After](shots/t005.png)

### Died outside pit

Invariant `die_outside`: Player must never die outside the pit.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: PawnAlive false at X 2176 Y \-334 which is outside pit 2350\-2650,350\-650, violates must never die outside pit

Repro:

Start from a fresh level load.

1. Walk to (1500, -500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (3500, 0)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t012_reset.png)

![After](shots/t014.png)

## Rejected hypotheses

None.
