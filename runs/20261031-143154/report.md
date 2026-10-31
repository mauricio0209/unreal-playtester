# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T14:31:54.004826 |
| Actions | 132 |
| Duration | 413.1 s |
| Cost | $0.2316 |

## Confirmed bugs

### Side door fails to open on interact up close

Invariant `side_door_opens_on_interact`: Interacting with the side door up close opens it regardless of inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Performed walk\_to 200,\-700 then interact while 46cm away; Inventory 0; ActorStates\.SideDoor remained closed after interact which should have opened it regardless of inventory\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t000.png)

![After](shots/t002.png)

### Gold coin adds 1 instead of 5

Invariant `gold_coin_worth_five`: Collecting the gold coin adds exactly 5 to inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Silver gave 2 \(inventory 2\), after gold inventory 3 \= delta 1 not 5, violates exactly 5\.

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

![Before](shots/t004_reset.png)

![After](shots/t007.png)

## Rejected hypotheses

None.
