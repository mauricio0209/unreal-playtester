# Session report

2 confirmed bugs, 1 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T14:45:47.648848 |
| Actions | 133 |
| Duration | 421.1 s |
| Cost | $0.2338 |

## Confirmed bugs

### Side door fails to open unconditionally

Invariant `side_door_opens_unconditionally`: Interacting with the side door up close opens it regardless of inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: At 156,\-686 \(<50cm from SideDoor\) interact with inventory 0 left SideDoor closed; screenshot shows wall/door not opened, state confirms closed, violating unconditional open\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Look at (200, -700, 150)
5. Press Interact
6. Let the game run for 1.0 s

![Before](shots/t002_reset.png)

![After](shots/t004.png)

### Gold coin only gives 1 instead of 5

Invariant `gold_coin_worth_five`: The gold coin adds 5 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to gold coin location \(1500,0\) from reset, GoldCoin went from present to missing while InventoryCount went from 0 to 1 \(delta 1 not 5\), violating worth 5 invariant

Repro:

Start from a fresh level load.

1. Walk to (1500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s

![Before](shots/t006_reset.png)

![After](shots/t008.png)

## Rejected hypotheses

### Exit door opens without gold coin

Invariant `exit_door_no_open_without_gold_interact`: Interacting with the exit door without the gold coin does nothing.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Interacted with ExitDoor at \~45cm with inventory 1 and GoldCoin missing \(not picked up\) yet ExitDoor transitioned closed\-\>open, violating no\-open\-without\-gold\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Look at (3500, 0, 150)
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t021_reset.png)

![After](shots/t024.png)
