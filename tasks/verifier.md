# Task: deterministic replay verifier (`agent/verifier.py`)

Create `agent/verifier.py`, `agent/test_verifier.py` and `agent/spec.json`. Python 3.14,
standard library only. Do not modify `agent/ue.py` or any other existing file. Run
`python3 agent/test_verifier.py` and make sure it passes before finishing.

## Context

An LLM explorer plays a game through `agent/ue.py` and files bug hypotheses. This verifier
decides, with no LLM involved, whether a hypothesis is a real, reproducible bug. It resets
the level, replays the repro steps, and evaluates a deterministic predicate on the recorded
states. A bug is confirmed only if the predicate holds in 3 out of 3 replays.

`ue.state()` returns a dict with: `StepId`, `bStepping`, `PawnAlive` (bool),
`PlayerLocation` {X,Y,Z}, `Velocity`, `LastZ` (last known pawn Z, kept after the pawn is
destroyed), `KillZ`, `bIsFalling`, `InventoryCount` (int), `BootTime`,
`ActorStates` {name: str} (e.g. {"Door1": "closed", "Pickup1": "present"}; a destroyed
actor is absent from the map), `ActorLocations` {name: {X,Y,Z}}.

`ue` exposes: `reset() -> state`, `step(seconds) -> state`, `move_to(x, y)`, `jump()`,
`look_at(x, y, z)`, `interact()`, `state()`. Actions other than `step` return nothing and
take effect during the next `step`.

## Repro steps format

A list of dicts, e.g.
`[{"action": "move_to", "x": 500, "y": 0}, {"action": "step", "seconds": 2.0}, {"action": "interact"}, {"action": "step", "seconds": 1.0}]`.
Allowed actions: `move_to`, `jump`, `look_at`, `interact`, `step`. Reject anything else
with `ValueError` before touching the game (this is a trust boundary: steps come from an LLM).

## `spec.json`

```json
{
  "invariants": [
    {"id": "no_fall_out_of_world", "description": "...", "predicate": "fell_out_of_world"},
    {"id": "door_opens", "description": "...", "predicate": "door_stays_closed_after_interact",
     "params": {"door": "Door1", "radius": 150}},
    {"id": "pickup_counts", "description": "...", "predicate": "pickup_not_counted",
     "params": {"pickup": "Pickup1"}}
  ],
  "intentional": [
    {"id": "decoy_pit", "description": "A pit the design wants players to fall into.",
     "region": {"min": {"X": 0, "Y": 0}, "max": {"X": 0, "Y": 0}}}
  ]
}
```
Write natural-language descriptions; leave the pit region at zeros (filled in later).

## API

```python
def load_spec(path) -> dict
def run_steps(ue, steps) -> list[dict]
    # ue.reset(), record the reset state, then execute steps in order. After every action
    # record {"action": step_dict, "state": ue.state()} (for `step`, use the state it returns).
    # Returns the trace: [{"action": None, "state": reset_state}, ...].
PREDICATES: dict[str, callable]   # name -> fn(trace, params, spec) -> bool (True = bug present)
def verify(ue, steps, invariant_id, spec, runs=3) -> dict
    # {"invariant": id, "confirmed": bool, "runs": [bool, ...], "reason": str}
    # Unknown invariant id -> confirmed False with a reason, no replay.
```

Predicates:
- `fell_out_of_world`: some state has `PawnAlive` false or `LastZ < KillZ`, AND the last known
  XY of the pawn before that is NOT inside any `intentional` region (XY box, inclusive).
  Falling inside an intentional region is not a bug.
- `door_stays_closed_after_interact`: there is an `interact` action whose preceding state has
  the pawn within `radius` cm (3D distance) of `ActorLocations[door]`, and every state from
  that action until the end of the trace still has `ActorStates[door] != "open"`, and the
  trace has at least one `step` after that interact.
- `pickup_not_counted`: the pickup is present in some state and absent in a later state,
  while `InventoryCount` in that later state equals the count in the last state where it was
  present.

## Tests

Use a fake `ue` object (a small class with the methods above, driven by scripted states), not
a real server. Cover: each predicate true and false; the decoy pit (fall inside the
intentional region) is not confirmed; `verify` confirms only when all 3 runs are true (a fake
that reproduces 2 of 3 times must not confirm); invalid action rejected with `ValueError`
and no `reset` called.
