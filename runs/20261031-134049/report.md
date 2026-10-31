# Session report

4 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T13:40:49.103619 |
| Actions | 152 |
| Duration | 538.1 s |
| Cost | $0.3477 |

## Confirmed bugs

### Blue door opened with key still present

Invariant `blue_needs_key`: Blue door stays shut with key present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to BlueDoor at 3500,0 and interacted with BlueKey still present, door state became open in state JSON, violating stays\-shut requirement

Repro:

Start from a fresh level load.

1. Let the game run for 0.5 s
2. Walk to (3500, 0)
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t011_reset.png)

![After](shots/t014.png)

### Red door stayed closed with red key

Invariant `red_opens`: Red door opens with red key.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up RedKey then interacted at RedDoor within range, but RedDoor remained closed, breaking red\_opens

Repro:

Start from a fresh level load.

1. Walk to (1500, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Press Interact
9. Let the game run for 1.0 s

![Before](shots/t014_reset.png)

![After](shots/t016.png)

### Gem bundle gave 1 not 3

Invariant `gem_three`: Gem bundle adds 3 to inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to GemBundle location, it went missing and InventoryCount went 0 to 1 instead of \+3, breaking gem\_three\.

Repro:

Start from a fresh level load.

1. Walk to (3000, -500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Walk to (2000, 300)
9. Let the game run for 1.0 s
10. Let the game run for 1.0 s
11. Let the game run for 1.0 s
12. Let the game run for 1.0 s

![Before](shots/t020_reset.png)

![After](shots/t023.png)

### Red door opened with key still present

Invariant `red_needs_key`: Red door stays shut with key present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: State shows RedDoor open and RedKey present after interact at door, so door opened without consuming key, breaking red\_needs\_key\.

Repro:

Start from a fresh level load.

1. Walk to (1200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Press Interact
6. Let the game run for 1.0 s
7. Walk to (300, 700)
8. Let the game run for 1.0 s
9. Let the game run for 1.0 s
10. Let the game run for 1.0 s
11. Let the game run for 1.0 s
12. Walk to (1200, -700)
13. Let the game run for 1.0 s
14. Let the game run for 1.0 s
15. Let the game run for 1.0 s
16. Press Interact
17. Let the game run for 1.0 s
18. Walk to (2200, -700)
19. Let the game run for 1.0 s
20. Let the game run for 1.0 s
21. Press Interact
22. Let the game run for 1.0 s

![Before](shots/t030_reset.png)

![After](shots/t035.png)

## Rejected hypotheses

None.
