# Submission text

As submitted to the Meta Global AI Developer Hackathon on 2026-11-03 (Indie track, Push the
Frontier).

## Project description

A designer writes the rules of a level in plain English. Muse Spark turns each rule into a check, plays the Unreal Engine 5.8 level on its own, and reports only the bugs a replay can prove.

The problem: playtesting is manual. Someone reads the design document, plays the level and checks every rule by hand, and small studios often have no QA team.

How it works (one command, no human in the loop):
1. Muse Spark writes one check per rule in a small JSON language. A plain interpreter runs them, so no model-written code ever runs.
2. Muse Spark plays from screenshots and game state and plans multi-step tests, like picking up a key and then trying a door.
3. A verifier with no AI reloads the level and replays the actions 3 times. Only bugs that reproduce 3/3 are reported, with the rule they break, the check, repro steps and a video.

Results, graded against an answer key the agent never sees:
- Vault: 2.7/3 bugs per session, 0 false positives. A bug that needs a key→door sequence: Muse Spark 6/6, a scripted bot with the same checks 0/6.
- Armory, a held-out level tested after the agent was frozen: Muse Spark Open 3.0/3.
- $0.18–0.40 per session. Limitations, including 2 false positives in 34 runs, are in the README.

Everything was built during the hackathon (Oct 30 – Nov 4).
Live report: https://mauricio0209.github.io/unreal-playtester/

## Use of Meta products

- Muse Spark 1.3 (Meta Model API): writes the checks from the design document, and plays the level with vision and reasoning.
- Muse Spark Open (meta-models/muse-spark-open-1026, open weights on Baseten): a drop-in explorer. On the held-out Armory level it found all 3 bugs in 4 of 4 sessions, with 0 false positives.
- Muse Code: wrote well-scoped modules headlessly, in sandboxed parallel lanes; every delegated commit says so.

## Why Meta's models are important

The core of the tool is judgment a script can't provide: reading a design document in plain English and turning each rule into a check, then playing a 3D level from screenshots and deciding what to test next. Muse Spark does both with vision and reasoning. Given the same checks, a scripted bot never found the bug that needs a sequence of steps (0/6); Muse Spark found it every time (6/6). Muse Spark Open runs the same agent on open weights, so a studio is not locked into one API.

## Links

- Demo video: https://youtu.be/95SwQI5UQwA
- Repository: https://github.com/mauricio0209/unreal-playtester
