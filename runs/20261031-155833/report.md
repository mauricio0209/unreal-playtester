# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:58:33.488491 |
| Actions | 155 |
| Duration | 318.4 s |
| Cost | $0.0701 |

## Confirmed bugs

### Death outside intentional pit

Invariant `no_fall_out_of_world`: The player pawn must never fall out of the world: die, drop below KillZ, or end up more than 2 m below the floor (Z < -200), except through a region the design marks as intentional. A fall anywhere else is a level geometry bug.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: PawnAlive false at X2179 Y\-489 Z6 which is outside decoy\_pit region 2350\-2650,350\-650, so death violates no\_fall\_out\_of\_world

Repro:

Start from a fresh level load.

1. Walk to (-400, -500)
2. Let the game run for 2.0 s
3. Walk to (4900, -500)
4. Let the game run for 2.0 s
5. Walk to (4900, -500)
6. Let the game run for 2.0 s
7. Walk to (4900, -500)
8. Let the game run for 2.0 s

![Before](shots/t001_lane7.png)

![After](shots/t001.png)

### Pickup1 missing but InventoryCount unchanged

Invariant `pickup_counts`: Collecting Pickup1 (it disappears from the world) must increase InventoryCount. If it is gone but the count is unchanged since it was last present, the pickup was lost.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: State shows Pickup1 state missing while InventoryCount is 0, so collecting/disappearance did not increase count, breaking pickup\_counts\.

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s

![Before](shots/t003_swept.png)

![After](shots/t004.png)

### Door1 stayed closed after in\-range interact

Invariant `door_opens`: Interacting with Door1 while standing within 150 cm of it must open the door. If the door is still not open after a later step, the interaction is broken.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at 45cm from Door1 interacted but state shows closed and view shows blank wall, so interaction failed

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 2.0 s
9. Look at (3500, 0, 150)
10. Press Interact
11. Let the game run for 2.0 s

![Before](shots/t009_reset.png)

![After](shots/t012.png)

## Rejected hypotheses

None.
