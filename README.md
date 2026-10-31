# Unreal AI Playtester

An autonomous playtesting agent for Unreal Engine 5.8, powered by Meta's Muse models.

Give it a level and the level's **design document in plain English**. Muse Spark reads the
document and writes its own checks for every rule, plays the level from screenshots and game
state, and files the bugs it finds. A deterministic verifier with **no LLM** confirms each one
by replaying it 3 times from a clean level load. Every confirmed bug comes with exact repro
steps, the check that caught it, and a replay video.

> Built for the Meta Global AI Developer Hackathon 2026. Everything here was made during the
> hackathon, starting 2026-10-30.

## Results

Three greybox levels, each with seeded bugs and controls (things that look suspicious but
work as designed). Every session is one command from a fresh level load. Vault and Armory are
graded by `scripts/grade_runs.py`, which replays every confirmed bug against an answer key
the agent never sees.

**Vault: logic bugs only the design document defines** (the model writes the checks).
The blue door opens without its key; the red door ignores the red key but opens with the green
one; a gem bundle worth 3 adds 1. The green door and the coin work and must not be filed.

| Explorer | Bugs found (mean) | Red door (needs a key→door sequence) | False positives | Mean time |
|---|---|---|---|---|
| Muse Spark 1.3 (Meta Model API), 6 sessions | **2.7 / 3** | **6 / 6** | 0 | 8.5 min |
| Muse Spark Open (Baseten), 6 sessions | **2.5 / 3** | 4 / 6 | 0 | 7.2 min |
| Scripted bot with the AI's checks, 6 runs | 1.7 / 3 | **0 / 6** | 0 | 2.9 min |
| Scripted bot alone | 0 / 3 | 0 | 0 | no checks to run |

**Armory: a held-out level** built after the agent was tuned on the Vault, with new mechanics
and inverted polarities: a side door that must never be locked but demands the silver coin, a
gold coin worth 5 that adds 1, and a floor hole outside a pit whose coordinates only the design
document gives. The exit door, the silver coin and the pit are controls.

| Explorer | Bugs found (mean) | All 3 | Floor hole (needs exploration) | False positives | Mean time |
|---|---|---|---|---|---|
| Muse Spark 1.3, 4 sessions | **2.8 / 3** | 3 / 4 | 4 / 4 | 1 | 9.1 min |
| Muse Spark Open, 4 sessions | **3.0 / 3** | **4 / 4** | 4 / 4 | 0 | 7.9 min |
| Scripted bot with the AI's checks, 8 runs | 1.9 / 3 | 0 / 8 | **0 / 8** | 1 | 1.2 min |

The first Armory run with the agent unchanged got the new door and coin rules right 16/16 with
no false positives, but found the floor hole only by chance (2/8); the lane sweep then became
available to any level with a fall rule (see the build log). The intentional pit was never
filed: falls into it were handed to the model, which ruled them out from the document's
coordinates.

**Arena: physical bugs with hand-written checks** (`agent/spec.json`). A floor without
collision, a door with a misaligned trigger, a pickup that does not count; a decoy pit and a
door that fails only on odd level loads must never be confirmed.

| Explorer | All 3 bugs | False positives | Intermittent door confirmed | Mean time |
|---|---|---|---|---|
| Muse Spark 1.3, 2 sessions | 2 / 2 | 0 | never | 5.1 min |
| Muse Spark Open, 2 sessions | 2 / 2 | 0 | never (filed twice, rejected twice) | 5.7 min |
| Scripted bot, 1 run | 1 / 1 | 0 | never | 6.8 min |

On Arena a plain script ties the AI: when a human already wrote every check, finding these
bugs is a sweep and a list of objects. That is why Vault and Armory exist.

**What the AI adds.** The scripted bot is given everything the AI produced except judgment:
the same checks, the same sweep, and an episode per object. It still never finds a bug that
needs a sequence (pick up a key, then try a door) or a judgment call (is this fall the pit the
document allows?), and without the AI it has no checks at all.

**Cost.** Reports price every token at the Standard rate ($1.25 / $4.25 per million input /
output tokens), what a studio would pay for a private game: about $0.07 per Arena session and
$0.18–0.40 per Vault or Armory session. This project ran on the Contributor tier
(`muse-spark-1.3-contributor`, $0.10 / $0.20), roughly 15 times cheaper. Contributor data may be
used for training, which is fine for a public greybox level and design document; use
`--model muse-spark-1.3` for a private game.

Every run in these tables is in the repository: the lists in `runs/*.txt` and, for each
run, `report.md`, `checks.json` and `session.json` (screenshots and videos are left out).
The agent version for these numbers: the agent is
frozen at tag `agent-freeze`; Vault numbers combine sessions from commits `1b1ba02` and
`e522dd2`, Armory and Arena numbers are from `e522dd2`.

## How it works

```
design doc (English) ──> Oracle: Muse Spark writes checks in a small JSON language
                           │  guards reject unknown names, checks that fire at load or
                           │  while idle; one review against the doc's rule sentences
                           v
[Python agent] ──HTTP──> [UE 5.8 PIE + Remote Control]  BP_TestHarness: GetState, MoveTo,
   │                                                     Interact, Jump, LookAt, Step,
   │                                                     Screenshot, ResetLevel, SetCamera
   ├─ Sweep:    if a check is about falling, measure the walkable area by walking to the
   │            walls, then walk lanes across it; every fall goes to the explorer to judge
   ├─ Explorer: Muse Spark sees screenshot + state + checks, plans action sequences
   │            (walk_to, interact, look_at, jump, step, reset), says which check it is
   │            testing, and files bug hypotheses
   ├─ Verifier: no LLM. Resets, replays the repro 3 times, evaluates the check on the
   │            recorded states. Confirmed only if it fails 3/3.
   └─ Report:   repro steps, check, before/after screenshots, verdict, replay video
```

- **The model never writes repro steps.** The repro is the list of actions actually executed
  since the last level reset, so the verifier replays exactly what happened.
- **The model never runs code.** Checks are JSON expressions (`agent/checks_reference.md`)
  interpreted by `agent/checks.py`; there is no `eval`.
- **The game is turn-based.** It stays paused while the model thinks and advances a fixed
  number of seconds per action at a fixed 30 fps, so replays are bit-identical and model
  latency never changes the outcome.

A check the model wrote for the Vault, as it appears in a run's `checks.json`:

```json
{"id": "red_door_opens_with_key",
 "description": "Interacting with the red door up close while carrying the red key opens it.",
 "violation": {"after": [{"and": [{"did": "interact"}, {"==": [{"var": "ActorStates.RedKey"}, null]},
                                  {"<": [{"dist": ["PlayerLocation", "ActorLocations.RedDoor"]}, 150]}]},
                         {"==": [{"var": "ActorStates.RedDoor"}, "closed"]}]}}
```

## Keeping false positives out

The verifier proves that a bug reproduces, not that the model's check is right. So:

- the oracle rejects checks that read names absent from the game state, fire on a fresh level
  load, fire while the player only waits, or have no real description, and feeds the reason
  back to the model;
- it asks again while objects are read by no check, and fails the session clearly when most
  stay unread;
- the explorer's hypotheses go through the verifier like everything else: in one Vault
  session Muse Spark filed a "red door won't open" bug from 160 cm away, out of range, and
  the replay rejected it.

## Known limitations

- **Session-to-session variance.** The same model on the same level finds 2 or 3 bugs; most
  misses are time or a wrong "I already tested that".
- **A wrong check can still be confirmed** if it fires reproducibly. 2 such false positives
  appeared in the 34 Vault and Armory runs above (20 agent sessions, 14 scripted runs reusing
  their checks), both from Muse Spark proximity rules read at a moment when the player had
  already walked past.
- **Lanes are 3 m apart** when the agent measures the area itself, so a hole narrower than
  that can slip between lanes.
- The harness exposes doors, pickups, the pawn and its inventory. Bugs that only show on
  screen (missing textures, clipping) are out of scope: they could not be verified without
  a model.

## Run it

```bash
cp .env.example .env   # META_API_KEY, BASETEN_API_KEY
```

Open `unreal/PlaytestArena` in UE 5.8, load a map (Arena, Vault or Armory), press Play, then:

```bash
python3 agent/session.py --level vault                      # Muse Spark on the Meta Model API
python3 agent/session.py --level armory --provider baseten  # Muse Spark Open on Baseten
python3 agent/session.py                                     # Arena, hand-written spec.json
python3 agent/session.py --level vault --provider script --checks runs/<run>/checks.json
python3 agent/check_seeded.py                                # Arena verifier check, no LLM
for t in agent/test_*.py; do python3 $t; done
```

A session writes `runs/<timestamp>/` with `report.md`, `checks.json`, screenshots and replay
videos. A new level is a map plus `agent/levels/<name>.md`.

Two editor instances run benchmarks twice as fast, with no clicks:

```bash
scripts/second_instance.sh Vault     # editor on a project copy (Remote Control 30011, MCP 8001)
PT_SESSION_ARGS=--no-video scripts/bench.sh vault runs/my_bench.txt meta baseten meta baseten
python3 scripts/grade_runs.py vault runs/my_bench.txt
```

## Muse Code usage

Well-scoped modules with a clear contract were delegated to Muse Code headlessly, up to three
lanes in parallel, then reviewed before commit: the verifier, the Remote Control client, the
session runner, the report, the replay videos, the scripted baseline, the check interpreter
and the oracle. Each prompt lives in `tasks/`, and each commit says `Delegated to Muse Code`.

```bash
scripts/muse-lane.sh <lane> tasks/<task>.md                     # muse-spark-1.3-contributor
scripts/muse-lane.sh <lane> tasks/<task>.md muse-wonder-1.0     # harder multi-file tasks
```

Each lane runs in its own git worktree under bubblewrap with `/mnt/c` hidden, so Muse never
sees `.env` (a canary test showed Muse's own sandbox does not restrict reads).

## Build log

The git history has every step; early commit messages are in Spanish, so here is the short
version in English.

- **Oct 30, setup and harness.** UE 5.8 project with Remote Control and the editor MCP server.
  `BP_TestHarness` built entirely through the MCP Blueprint tools. Fixed 30 fps: the same
  replay gives bit-identical positions across PIE sessions, which is what makes 3/3
  verification meaningful. Reasoning tokens count against `max_tokens`, so budgets are large.
- **Oct 30, Muse Code isolation.** Every delegated lane runs under bubblewrap in its own
  worktree with `.env` invisible.
- **Oct 30, agent loop on Arena.** Repro steps come from executed actions, never from the
  model. Fixes along the way: remembering filed bugs, batching up to 4 actions per turn,
  marking vanished objects, `reasoning_effort: low`, counting a pawn 2 m under the floor as
  fallen even before it dies.
- **Oct 31, intermittent bug, open weights, video.** `Door2` fails only on odd loads and is
  never confirmed. Muse Spark Open on Baseten as a drop-in explorer. A replay video per bug,
  recorded from a chase camera (`SetCamera`) because the first-person view only showed the
  wall in front of a door.
- **Oct 31, the honest question.** A scripted bot found all of Arena's bugs at $0. So the
  project pivoted: the model writes the checks from a design document (the Vault level), and
  a scripted baseline runs in every benchmark.
- **Oct 31, what the Vault benchmarks exposed**, fixed one at a time:
  - one stray bracket in the model's JSON discarded every check: checks now come one per
    line and a malformed line only loses itself;
  - the model wrote "the red door must not open without its key" but not "must open with
    it", so it saw the bug and could not file it: the oracle now asks for both sides;
  - Baseten retested the same door until the deadline: each action names the check it tests,
    the agent sees untested checks every turn, and "done" is refused while any is untested;
  - one reply produced checks named `d1`…`d17` described as "d", confirmed as 5 false
    positives: guards for idle-firing checks and empty descriptions;
  - keyword grading counted "RedKey vanished" as the red door bug: grading is now a replay
    against an answer key.
- **Oct 31, held-out level.** The Armory was built after tuning and run with the agent
  unchanged. Doors and coins generalized; the floor hole did not, so the agent now measures
  the walkable area itself and sweeps it whenever a check is about falling, and the oracle
  reviews its checks against the document's rule sentences. Arena and Vault were rerun to
  check nothing regressed, and the agent was frozen.
- **Oct 31, two editors.** A second editor instance on a project copy, started and driven
  through its own MCP server, runs benchmarks in parallel.

## Repository layout

- `agent/`: oracle, check interpreter, explorer, scripted baseline, verifier, report, replay
  videos and the session runner (standard library only). `agent/levels/` holds the design
  documents, `agent/spec.json` Arena's hand-written checks.
- `scripts/`: benchmark runner, second editor instance, MCP client, graders, Muse Code lanes.
- `tasks/`: the prompts given to Muse Code for each delegated module.
- `unreal/PlaytestArena/`: UE 5.8 project with the three levels and `BP_TestHarness`.
