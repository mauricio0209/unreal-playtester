# Session report

4 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T13:31:31.216381 |
| Actions | 166 |
| Duration | 557.4 s |
| Cost | $0.3716 |

## Confirmed bugs

### Blue door opened without carrying blue key

Invariant `blue_door_needs_key`: Blue door opens only if blue key is carried.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Interacted at blue door with inventory 0 and BlueKey present, BlueDoor state is open in screenshot/state, so door opened without key

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

![Before](shots/t004_reset.png)

![After](shots/t006.png)

### Gem bundle added only 1 to inventory

Invariant `gem_worth_three`: Collecting the gem bundle adds 3 to inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Coin pickup raised inventory 0 to 1, then gem pickup raised it 1 to 2 instead of 1 to 4, so gem worth is 1 not 3

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s
5. Walk to (2000, 300)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 2.0 s

![Before](shots/t006_reset.png)

![After](shots/t009.png)

### Red door did not open with red key

Invariant `red_door_opens_with_key`: Interacting next to red door while carrying red key opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up RedKey \(missing/carried\) then interacted within \~50cm of RedDoor at 2200,\-700, door remained closed, breaking open\-with\-key requirement

Repro:

Start from a fresh level load.

1. Walk to (1500, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Look at (2200, -700, 150)
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t012_reset.png)

![After](shots/t015.png)

### Red door opened without red key

Invariant `red_door_needs_key`: Red door opens only if red key is carried.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: State shows RedDoor open while RedKey is still present on ground and GreenKey is carried, so interacting at red door with wrong key opened it, violating needs key\.

Repro:

Start from a fresh level load.

1. Walk to (300, 700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Let the game run for 1.0 s
10. Look at (2200, -700, 150)
11. Press Interact
12. Let the game run for 1.0 s

![Before](shots/t017_reset.png)

![After](shots/t020.png)

## Rejected hypotheses

None.
