# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T14:40:49.138276 |
| Actions | 100 |
| Duration | 448.5 s |
| Cost | $0.2205 |

## Confirmed bugs

### Side door did not open on interact

Invariant `side_door_opens`: Standing next to the side door and interacting with it opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at \~46cm from SideDoor, interacted, but ActorStates\.SideDoor remains closed, violating side\_door\_opens

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s
5. Press Interact
6. Let the game run for 1.0 s

![Before](shots/t000.png)

![After](shots/t003.png)

### Gold coin adds 1 instead of 5

Invariant `gold_worth_five`: The gold coin adds 5 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up silver then gold: inventory went 0\-\>2 then 2\-\>3, so gold delta was 1 not 5, breaking gold\_worth\_five

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s
5. Walk to (1500, 0)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 2.0 s

![Before](shots/t003_reset.png)

![After](shots/t006.png)

## Rejected hypotheses

None.
