# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T14:25:05.608854 |
| Actions | 129 |
| Duration | 408.2 s |
| Cost | $0.2103 |

## Confirmed bugs

### Gold coin gives 1 instead of 5

Invariant `gold_coin_worth_five`: The gold coin is worth 5 when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected silver correctly gave 2, then gold changed inventory from 2 to 3 \(delta 1\) not 5, breaking worth invariant

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s
5. Walk to (1500, 0)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.5 s

![Before](shots/t002_reset.png)

![After](shots/t005.png)

### Side door does not open on interact

Invariant `side_door_opens_on_interact`: In the west hall the side door is never locked and opens when a player standing next to it interacts.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at \~46cm from SideDoor interacted and state remained closed instead of opening

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t010_reset.png)

![After](shots/t012.png)

## Rejected hypotheses

None.
