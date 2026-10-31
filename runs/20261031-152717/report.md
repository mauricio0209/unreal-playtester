# Session report

4 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:27:17.625988 |
| Actions | 168 |
| Duration | 591.2 s |
| Cost | $0.315 |

## Confirmed bugs

### Death outside pit at sweep lane y\=\-365

Invariant `no_death_outside_pit`: The player never dies outside the pit.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at X2166 Y\-357 Z11 with PawnAlive false is outside pit bounds X2350\-2650 Y350\-650, so dying here breaks no\_death\_outside\_pit\. Screenshot shows falling under floor\.

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

### Side door stays closed with empty pockets

Invariant `side_door_opens_empty`: Standing next to the side door and interacting with empty pockets opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Interacted next to SideDoor with inventory 0 and it remained closed, state shows closed, breaking open expectation

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Press Interact
6. Let the game run for 1.0 s

![Before](shots/t003_swept.png)

![After](shots/t005.png)

### Fell through floor outside pit

Invariant `no_fall_through_floor_outside_pit`: The player never ends up below the floor outside the pit.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at X\=2176 Y\=\-334 Z\=2 \(Z<50 outside pit 2350\-2650,350\-650\) dead with blue void view, so player ended below floor outside pit\.

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

![Before](shots/t009_reset.png)

![After](shots/t011.png)

### Gold coin adds 1 instead of 5

Invariant `gold_worth_five`: The gold coin adds 5 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected silver to reach 2 then gold to reach 3, delta 1 not 5, state shows both missing with inventory 3

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (3500, 0)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Let the game run for 1.0 s
10. Let the game run for 1.0 s
11. Let the game run for 1.0 s
12. Press Interact
13. Let the game run for 1.0 s
14. Walk to (1500, 0)
15. Let the game run for 1.0 s
16. Let the game run for 1.0 s
17. Let the game run for 1.0 s
18. Let the game run for 1.0 s
19. Let the game run for 1.0 s

![Before](shots/t011_reset.png)

![After](shots/t016.png)

## Rejected hypotheses

None.
