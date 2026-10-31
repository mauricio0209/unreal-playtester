# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:09:42.555182 |
| Actions | 160 |
| Duration | 526.6 s |
| Cost | $0.3106 |

## Confirmed bugs

### Death outside pit at \(2166,\-357\)

Invariant `death_only_in_pit`: The player never dies outside the pit.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: PawnAlive false at X\=2166 Y\=\-357 which is outside pit bounds 2350\-2650,350\-650, so death occurred outside pit

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

### Side door did not open on nearby interact

Invariant `side_door_opens`: The side door opens when interacted with from nearby.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: At \~46cm from SideDoor I interacted and state stayed closed, image shows wall up close, breaking side\_door\_opens

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t004_swept.png)

![After](shots/t006.png)

### Gold coin gave 1 instead of 5

Invariant `gold_worth_five`: The gold coin adds 5 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up gold going from \(978,489\) to \(1484,15\): Silver correctly made 0\-\>2, but gold made 2\-\>3 \(\+1 not \+5\), violating gold worth 5\. Observed state shows both coins missing with InventoryCount 3\.

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

![Before](shots/t008_reset.png)

![After](shots/t011.png)

## Rejected hypotheses

None.
