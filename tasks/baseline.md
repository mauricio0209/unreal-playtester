# Task: scripted baseline explorer (`agent/baseline.py`)

Create `agent/baseline.py` and `agent/test_baseline.py`, and wire the baseline into
`agent/session.py` (plus a test in `agent/test_session.py`). Python 3.14, standard library
only. Do not modify any other file. Run every `agent/test_*.py` and make sure all pass
before finishing.

## Why

The project's explorer uses an LLM (Muse Spark) to play a level and file bug hypotheses.
We need an honest baseline with **no LLM at all**, to compare against in the benchmark.
It must use the same interface as `explorer.explore` so `session.py` verifies and reports
its hypotheses exactly the same way.

## Read first

- `agent/explorer.py`: `explore(ue, llm, spec, shots_dir, max_turns, deadline_s, log)`,
  `sweep_lanes(spec)`, `_do(ue, step)`, `_shot(ue, shots_dir, name)`, and the hypothesis dict
  shape it returns: `{"title", "hypothesis", "invariant", "steps", "before", "after"}`, and
  `{"hypotheses": [...], "actions": <int>}` overall.
- `agent/verifier.py`: `PREDICATES` (name -> `fn(trace, params, spec) -> bool`) and the trace
  format `[{"action": None, "state": reset_state}, {"action": step_dict, "state": state}, ...]`.
- `agent/session.py`: how `--provider`, the LLM client and `explorer_mod` are created.
- `agent/spec.json`: invariants with `predicate` and `params`, and `intentional` regions.

## `baseline.explore(ue, llm, spec, shots_dir, max_turns=40, deadline_s=360.0, log=print)`

Same signature as `explorer.explore`; `llm` and `max_turns` are ignored. It runs a list of
**episodes**. Each episode: `ue.reset()`, take a `before` screenshot with `explorer._shot`,
execute its steps with `explorer._do`, building a verifier-format trace as it goes, then take
an `after` screenshot. Stop starting new episodes once `deadline_s` has elapsed
(`time.monotonic()`).

Episodes, in order:
1. One per lane from `explorer.sweep_lanes(spec)` (the first element of its return value).
2. One per object name in the reset state's `ActorStates`, sorted by name, using the object's
   `ActorLocations` entry: `move_to(X, Y)`, then enough `step`s of at most 8.0 s to cover the
   straight-line distance from the reset `PlayerLocation` at 600 cm/s plus 1 s, then
   `interact`, `step 1.0`, `step 1.0`. (Walking into a pickup collects it; a door stops the
   pawn in front of it, within interaction range.)

After each step of an episode, evaluate every invariant's predicate on the trace so far
(`verifier.PREDICATES[inv["predicate"]](trace, inv.get("params", {}), spec)`; skip
invariants whose predicate is unknown). The first time an invariant's predicate holds, file a
hypothesis for it with `steps` = the episode's steps up to and including that step, a fixed
`title` like `"<invariant id> broken (scripted check)"` and a short `hypothesis` text. File
each invariant at most once per session. If the pawn is dead (`PawnAlive` false), end the
episode. Log one line per episode and one per filed hypothesis via `log`.

Return `{"hypotheses": [...], "actions": <number of actions executed>}`.

## `session.py`

Add `"script"` to the `--provider` choices. With `--provider script`, do not create an LLM
client (pass `None`) and use `baseline` as the explorer module (unless `explorer_mod` is
injected, as tests do). Cost must come out as 0. Keep everything else unchanged.

## Tests (`agent/test_baseline.py`, same style as `agent/test_explorer.py`)

Use a fake `ue` (no real engine). Cover at least:
- an object episode that exposes a door that stays closed files `door_opens` with steps ending
  at the step where the predicate first held;
- a fall during a sweep lane files the fall invariant, and a fall inside an `intentional`
  region does not;
- an invariant is never filed twice;
- the deadline stops new episodes.

Plus one test in `agent/test_session.py` that `--provider script` runs without an LLM client.
