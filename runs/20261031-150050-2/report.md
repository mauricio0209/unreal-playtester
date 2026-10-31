# Session report

3 confirmed bugs, 3 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:00:50.600361 |
| Actions | 141 |
| Duration | 524.4 s |
| Cost | $0.1768 |

## Confirmed bugs

### Death outside pit on sweep lane y\=\-365

Invariant `no_death_outside_pit`: The player must never die outside the pit (x 2350-2650, y 350-650).

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at 2166,\-357 Z11 alive\=false outside pit bounds 2350\-2650,350\-650\. Death outside pit violates invariant\.

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

### Gold coin only adds 1 instead of 5

Invariant `gold_coin_worth_five`: The gold coin adds 5 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected silver gave 2, then gold went missing but inventory only increased from 2 to 3 \(delta 1\), not 5 as spec requires\. Automatic check correctly flags\.

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

![Before](shots/t003_swept.png)

![After](shots/t005.png)

### Side door fails to open on interact

Invariant `side_door_opens_on_interact`: Standing next to the side door and interacting opens it, with or without inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Stood within \~75cm of SideDoor at \(200,\-700\) and interacted; Door remained closed \(state\=closed\) violating spec that it should open with or without inventory\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (200, -700)
6. Let the game run for 1.0 s
7. Press Interact
8. Let the game run for 1.0 s

![Before](shots/t005_reset.png)

![After](shots/t008.png)

## Rejected hypotheses

### Pit fall does not kill player

Invariant `pit_fall_ends_attempt`: Falling into the pit (x 2350-2650, y 350-650) is intended and must end the attempt with death.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Player at X2579 Y533 Z\-417 inside pit bounds is falling but PawnAlive remains true, should have died when Z below \-20\.

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

![Before](shots/t002_lane1.png)

![After](shots/t002.png)

### Exit door opens without gold coin on interact

Invariant `exit_door_interact_does_nothing_without_gold`: Without the gold coin, interacting with the exit door does nothing and it stays closed.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: t9\-10: at ExitDoor \(3455,0\) with GoldCoin\=missing and inventory 1, interact changed ExitDoor from closed to open, violating stays closed without gold\.

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
9. Walk to (3500, 0)
10. Let the game run for 1.0 s
11. Let the game run for 1.0 s
12. Let the game run for 1.0 s
13. Let the game run for 1.0 s
14. Press Interact
15. Let the game run for 1.0 s

![Before](shots/t016_reset.png)

![After](shots/t020.png)

### Silver coin only adds 1 instead of 2

Invariant `silver_coin_worth_two`: The silver coin adds 2 to inventory when collected.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Collected SilverCoin at 1000,500: Inventory went from 1 to 2 \(delta 1\) but spec requires \+2\.

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s

![Before](shots/t020_reset.png)

![After](shots/t022.png)
