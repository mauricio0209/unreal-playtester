# Session report

3 confirmed bugs, 2 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:17:07.782728 |
| Actions | 167 |
| Duration | 483.7 s |
| Cost | $0.1855 |

## Confirmed bugs

### Floor not solid outside pit \- fell through at \(2166,\-357\)

Invariant `floor_solid_outside_pit`: Outside the pit (x 2350-2650 y 350-650) the floor is solid: the player must never die or fall below the floor.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted sweep at y\=\-365 caused death at X\=2166 Y\=\-357 Z\=11 outside pit bounds \(2350\-2650,350\-650\)\. Floor should be solid outside pit but player died/fell through\.

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

### Side door did not open on interact

Invariant `side_door_opens_when_interacted`: The side door is never locked: interacting next to it opens it with or without items.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Interacted at 46cm from SideDoor but state stayed closed, image shows closed door/wall, violating never\-locked expectation

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t003_swept.png)

![After](shots/t004.png)

### Gold coin added only 1 instead of 5

Invariant `gold_coin_worth_five`: The gold coin is worth 5 and adds 5 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected silver gave 2 as expected \(inventory 2\), then collecting gold at \~1500,0 increased inventory from 2 to 3 instead of to 7, violating worth 5\.

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

![Before](shots/t006_reset.png)

![After](shots/t009.png)

## Rejected hypotheses

### Pit kills player instead of ending attempt alive

Invariant `pit_ends_attempt`: Falling into the pit from x 2350 to 2650 and y 350 to 650 is intended and ends the attempt.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Player at pit coordinates 2350\-2650/350\-650 Z\=5 has PawnAlive\=false, but spec says after entering pit PawnAlive must remain true; the pit incorrectly causes death\.

Repro:

Start from a fresh level load.

1. Walk to (2500, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 2.0 s

![Before](shots/t011_reset.png)

![After](shots/t013.png)

### Exit door opened without gold coin

Invariant `exit_door_stays_locked_without_gold`: The exit door opens only for a player carrying the gold coin; without it the door stays closed.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Interacted at ExitDoor at \~3455,0 with Inventory 1 and GoldCoin not collected \(state missing/present\), door state became open, violating requirement that exit stays closed unless carrying gold\.

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

![Before](shots/t019_reset.png)

![After](shots/t021.png)
