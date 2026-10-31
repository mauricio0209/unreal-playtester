# Session report

4 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T15:40:41.883340 |
| Actions | 113 |
| Duration | 450.3 s |
| Cost | $0.3121 |

## Confirmed bugs

### Gem bundle gave only 1 instead of 3

Invariant `gem_bundle_worth_three`: A gem bundle is worth 3.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to gem bundle location, GemBundle went missing and InventoryCount went 0 to 1, not \+3, breaking worth\-3 rule

Repro:

Start from a fresh level load.

1. Let the game run for 0.5 s
2. Walk to (2000, 300)
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 0.5 s

![Before](shots/t002_reset.png)

![After](shots/t005.png)

### Red door did not open with red key

Invariant `red_door_opens_with_key`: With the red key, interacting with the red door next to it opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up RedKey then interacted next to RedDoor at \~44cm, RedDoor state remains closed in state JSON and view shows closed door, breaking opens\-with\-key requirement\.

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

![Before](shots/t008_reset.png)

![After](shots/t010.png)

### Green key opened red door

Invariant `key_opens_only_own_color`: A key opens only the door of its own color.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked GreenKey \(missing\) left RedKey present, interacted at RedDoor and it is open, so a key opened a different color door

Repro:

Start from a fresh level load.

1. Walk to (300, 700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Let the game run for 1.0 s
10. Press Interact
11. Let the game run for 1.0 s

![Before](shots/t012_reset.png)

![After](shots/t015.png)

### Red door opened without red key

Invariant `door_needs_matching_key`: A door opens only if the player is carrying the key of the same color.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: State shows RedDoor open while RedKey is still present on ground and GreenKey is missing \(carried\), so door opened without carrying matching key, violating door needs matching key\.

Repro:

Start from a fresh level load.

1. Walk to (300, 700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Let the game run for 1.0 s
10. Press Interact
11. Let the game run for 1.0 s

![Before](shots/t025_reset.png)

![After](shots/t028.png)

## Rejected hypotheses

None.
