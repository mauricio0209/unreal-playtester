# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:00:50.600593 |
| Actions | 183 |
| Duration | 531.8 s |
| Cost | $0.2561 |

## Confirmed bugs

### Died outside pit area

Invariant `never_die_outside_pit`: Player never dies outside the pit.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at 2166,\-357 died while outside pit X 2350\-2650 Y 350\-650, violates never die outside pit\.

Repro:

Start from a fresh level load.

1. Walk to (-466, -365)
2. Let the game run for 2.0 s
3. Walk to (3456, -365)
4. Let the game run for 2.0 s
5. Walk to (3456, -365)
6. Let the game run for 2.0 s
7. Walk to (3456, -365)
8. Let the game run for 2.0 s

![Before](shots/t001_lane4.png)

![After](shots/t001.png)

### Gold gave 1 not 5

Invariant `gold_worth_five`: Gold coin adds exactly 5 to inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: GoldCoin is missing and InventoryCount is 1, so pickup added 1 instead of 5, violating gold worth 5

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
9. Let the game run for 0.5 s

![Before](shots/t003_swept.png)

![After](shots/t004.png)

## Rejected hypotheses

None.
