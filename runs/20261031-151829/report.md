# Session report

4 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:18:29.276937 |
| Actions | 170 |
| Duration | 528.2 s |
| Cost | $0.2728 |

## Confirmed bugs

### Died outside pit

Invariant `never_die_outside_pit`: The player must never die outside the pit from x 2350 to 2650 and y 350 to 650.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player died at X 2166 Y \-357 which is outside pit 2350\-2650,350\-650 with PawnAlive false, violating never die outside pit\.

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

### Silver collected without walking over it

Invariant `silver_walkover`: The silver coin is collected only by walking over it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: SilverCoin is missing with Inventory 2 while player is at 2566,530 far from pickup, so collection occurred without proximity per auto\-check

Repro:

Start from a fresh level load.

1. Walk to (-466, 535)
2. Let the game run for 2.0 s
3. Walk to (3456, 535)
4. Let the game run for 2.0 s
5. Walk to (3456, 535)
6. Let the game run for 2.0 s
7. Walk to (3456, 535)
8. Let the game run for 2.0 s
9. Let the game run for 3.0 s

![Before](shots/t002_lane1.png)

![After](shots/t003.png)

### Side door stayed closed after interact

Invariant `side_door_opens`: Interacting next to the side door opens it with or without anything in their pockets.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at 156,\-686 within 50cm of SideDoor at 200,\-700, did interact, but state still closed and view shows wall/door not opened, breaking side\_door\_opens

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t004_swept.png)

![After](shots/t005.png)

### Gold coin added only 1

Invariant `gold_worth_five`: Collecting the gold coin adds exactly 5 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Went from inventory 2 with Gold present to 3 with Gold missing after walking over gold, delta 1 not 5, breaking worth\.

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

![Before](shots/t005_reset.png)

![After](shots/t008.png)

## Rejected hypotheses

None.
