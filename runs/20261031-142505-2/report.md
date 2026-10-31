# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T14:25:05.608749 |
| Actions | 149 |
| Duration | 461.0 s |
| Cost | $0.2692 |

## Confirmed bugs

### Side door did not open on interact

Invariant `side_door_opens`: Standing next to the side door and interacting opens it with or without anything in pockets.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to 200,\-700 and interacted within \~50cm with empty inventory but SideDoor state remains closed, violating should\-open behavior\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t000.png)

![After](shots/t002.png)

### Gold coin gave only 1 instead of 5

Invariant `gold_worth_five`: The gold coin adds 5 to the inventory count.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked silver to 2 then gold to 3, delta 1 not 5, breaking gold\_worth\_five

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

### Fell through floor outside pit

Invariant `floor_solid_outside_pit`: Outside the pit the player must never fall through the floor, die, or end up below the floor.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player died at X2176 Y\-334 Z2 which is outside pit bounds 2350\-2650,350\-650, with Z<50 and PawnAlive false, breaking floor solidity\.

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

![Before](shots/t016_reset.png)

![After](shots/t018.png)

## Rejected hypotheses

None.
