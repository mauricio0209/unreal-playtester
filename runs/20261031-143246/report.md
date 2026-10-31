# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T14:32:46.822302 |
| Actions | 112 |
| Duration | 482.2 s |
| Cost | $0.2559 |

## Confirmed bugs

### Side door stayed closed after close interact

Invariant `side_door_opens`: Interacting with the side door from up close opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: At \~46cm from SideDoor I interacted and state stayed closed, image shows facing wall/door, breaking side\_door\_opens

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

### Gold coin added 1 not 5

Invariant `gold_worth_five`: The gold coin adds 5 to the inventory count.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked silver to reach inventory 2 then picked gold to reach 3, increase of 1 not 5, state shows both coins missing

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
