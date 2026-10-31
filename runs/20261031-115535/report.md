# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model |  |
| Started | 2026-10-31T11:55:35.034885 |
| Actions | 40 |
| Duration | 232.7 s |
| Cost | $0.0 |

## Confirmed bugs

### blue\_door\_needs\_key broken \(scripted check\)

Invariant `blue_door_needs_key`: Blue door must not be open while blue key is still present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object BlueDoor episode broke blue\_door\_needs\_key\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 6.833333333333333 s
3. Press Interact

![Replay](videos/bug1.gif)

[Replay video (MP4)](videos/bug1.mp4)

![Before](shots/baseline_000_before.png)

![After](shots/baseline_000_after.png)

### gem\_bundle\_worth\_three broken \(scripted check\)

Invariant `gem_bundle_worth_three`: Gem bundle adds exactly 3 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object GemBundle episode broke gem\_bundle\_worth\_three\.

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 4.370624736026114 s

![Replay](videos/bug2.gif)

[Replay video (MP4)](videos/bug2.mp4)

![Before](shots/baseline_003_before.png)

![After](shots/baseline_003_after.png)

### loot\_never\_disappears\_without\_inventory broken \(scripted check\)

Invariant `loot_never_disappears_without_inventory`: Loot must not disappear without its inventory value being added.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object GemBundle episode broke loot\_never\_disappears\_without\_inventory\.

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 4.370624736026114 s
3. Press Interact

![Replay](videos/bug3.gif)

[Replay video (MP4)](videos/bug3.mp4)

![Before](shots/baseline_003_before.png)

![After](shots/baseline_003_after.png)

## Rejected hypotheses

None.
