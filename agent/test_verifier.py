"""Tests for verifier.py using a fake ue object. Run: python3 agent/test_verifier.py"""

import os

import verifier


def make_state(**overrides):
    state = {
        "StepId": 0,
        "bStepping": False,
        "PawnAlive": True,
        "PlayerLocation": {"X": 0, "Y": 0, "Z": 100},
        "Velocity": {"X": 0, "Y": 0, "Z": 0},
        "LastZ": 100,
        "KillZ": -1000,
        "bIsFalling": False,
        "InventoryCount": 0,
        "BootTime": 0.0,
        "ActorStates": {},
        "ActorLocations": {},
    }
    state.update(overrides)
    return state


class FakeUE:
    """Scripted ue double. Each run is a list of states, one per trace entry.

    reset() starts the next run; every mutating action advances to the next
    scripted state; state() returns the current one without advancing.
    """

    def __init__(self, runs):
        self._runs = runs
        self.resets = 0
        self.state_calls = 0
        self.log = []

    def reset(self):
        self.resets += 1
        index = min(self.resets - 1, len(self._runs) - 1)
        self._states = self._run_states(index)
        self._i = 0
        self.log.append(("reset",))
        return self._states[0]

    def _run_states(self, index):
        return self._runs[index]

    def _advance(self, name):
        self.log.append((name,))
        if self._i + 1 < len(self._states):
            self._i += 1
        return self._states[self._i]

    def step(self, seconds):
        return self._advance("step")

    def move_to(self, x, y):
        return self._advance("move_to")

    def jump(self):
        return self._advance("jump")

    def look_at(self, x, y, z):
        return self._advance("look_at")

    def interact(self):
        return self._advance("interact")

    def state(self):
        self.state_calls += 1
        return self._states[self._i]


def base_spec(**overrides):
    spec = {
        "invariants": [
            {"id": "no_fall_out_of_world", "predicate": "fell_out_of_world",
             "params": {}},
            {"id": "door_opens",
             "predicate": "door_stays_closed_after_interact",
             "params": {"door": "Door1", "radius": 150}},
            {"id": "pickup_counts", "predicate": "pickup_not_counted",
             "params": {"pickup": "Pickup1"}},
        ],
        "intentional": [],
    }
    spec.update(overrides)
    return spec


def trace_of(*states, actions=None):
    entries = [{"action": None, "state": states[0]}]
    for i, state in enumerate(states[1:]):
        action = {"action": "step", "seconds": 1.0}
        if actions is not None:
            action = actions[i]
        entries.append({"action": action, "state": state})
    return entries


# --- fell_out_of_world ---

def t_fell_true_dead():
    spec = base_spec()
    trace = trace_of(
        make_state(),
        make_state(PawnAlive=False, LastZ=-2000,
                   PlayerLocation={"X": 500, "Y": 500, "Z": -2000}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](trace, {}, spec) is True


def t_fell_true_below_killz():
    spec = base_spec()
    trace = trace_of(
        make_state(),
        make_state(PawnAlive=True, LastZ=-1500,
                   PlayerLocation={"X": 500, "Y": 500, "Z": -1500}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](trace, {}, spec) is True


def t_fell_false_healthy():
    spec = base_spec()
    trace = trace_of(
        make_state(),
        make_state(PlayerLocation={"X": 500, "Y": 500, "Z": 90}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](trace, {}, spec) is False


def t_decoy_pit_not_a_bug():
    spec = base_spec(intentional=[
        {"id": "decoy_pit", "description": "d",
         "region": {"min": {"X": 400, "Y": 400}, "max": {"X": 600, "Y": 600}}}
    ])
    trace = trace_of(
        make_state(),
        make_state(PawnAlive=False, LastZ=-2000,
                   PlayerLocation={"X": 500, "Y": 500, "Z": -2000}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](trace, {}, spec) is False
    # Same fall outside the region is still a bug.
    outside = trace_of(
        make_state(),
        make_state(PawnAlive=False, LastZ=-2000,
                   PlayerLocation={"X": 900, "Y": 900, "Z": -2000}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](outside, {}, spec) is True


def t_decoy_pit_entered_during_long_step():
    # The previous sample is far from the pit; the harness reports the last
    # known location on the death state, so that is what decides.
    spec = base_spec(intentional=[
        {"id": "decoy_pit", "description": "d",
         "region": {"min": {"X": 400, "Y": 400}, "max": {"X": 600, "Y": 600}}}
    ])
    trace = trace_of(
        make_state(PlayerLocation={"X": 0, "Y": 0, "Z": 100}),
        make_state(PawnAlive=False, LastZ=-1001,
                   PlayerLocation={"X": 500, "Y": 500, "Z": -1001}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](trace, {}, spec) is False


def t_decoy_pit_boundary_inclusive():
    spec = base_spec(intentional=[
        {"id": "decoy_pit", "description": "d",
         "region": {"min": {"X": 400, "Y": 400}, "max": {"X": 600, "Y": 600}}}
    ])
    trace = trace_of(
        make_state(),
        make_state(PawnAlive=False, LastZ=-2000,
                   PlayerLocation={"X": 400, "Y": 600, "Z": -2000}),
    )
    assert verifier.PREDICATES["fell_out_of_world"](trace, {}, spec) is False


# --- door_stays_closed_after_interact ---

def door_trace(door_state_before, door_state_after, player_xy=(0, 0),
               step_after=True):
    door_loc = {"X": 100, "Y": 0, "Z": 100}
    before = make_state(
        PlayerLocation={"X": player_xy[0], "Y": player_xy[1], "Z": 100},
        ActorStates={"Door1": door_state_before},
        ActorLocations={"Door1": dict(door_loc)},
    )
    after = make_state(
        PlayerLocation={"X": player_xy[0], "Y": player_xy[1], "Z": 100},
        ActorStates={} if door_state_after is None else {"Door1": door_state_after},
        ActorLocations={"Door1": dict(door_loc)},
    )
    actions = [{"action": "interact"}]
    states = [before, before]
    if step_after:
        actions.append({"action": "step", "seconds": 1.0})
    else:
        actions.append({"action": "jump"})
    states.append(after)
    trace = trace_of(*states, actions=actions)
    if not step_after:
        # A non-step trailing action: no step exists after the interact.
        assert not any(
            isinstance(e["action"], dict) and e["action"].get("action") == "step"
            for e in trace[1:]
        )
    return trace


def t_door_true_stays_closed():
    spec = base_spec()
    params = {"door": "Door1", "radius": 150}
    trace = door_trace("closed", "closed", player_xy=(0, 0))
    assert verifier.PREDICATES["door_stays_closed_after_interact"](
        trace, params, spec) is True


def t_door_false_opened():
    spec = base_spec()
    params = {"door": "Door1", "radius": 150}
    trace = door_trace("closed", "open", player_xy=(0, 0))
    assert verifier.PREDICATES["door_stays_closed_after_interact"](
        trace, params, spec) is False


def t_door_false_too_far():
    spec = base_spec()
    params = {"door": "Door1", "radius": 150}
    trace = door_trace("closed", "closed", player_xy=(5000, 5000))
    assert verifier.PREDICATES["door_stays_closed_after_interact"](
        trace, params, spec) is False


def t_door_false_no_step_after():
    spec = base_spec()
    params = {"door": "Door1", "radius": 150}
    trace = door_trace("closed", "closed", player_xy=(0, 0), step_after=False)
    assert verifier.PREDICATES["door_stays_closed_after_interact"](
        trace, params, spec) is False


# --- pickup_not_counted ---

def t_pickup_true_lost():
    spec = base_spec()
    params = {"pickup": "Pickup1"}
    trace = trace_of(
        make_state(ActorStates={"Pickup1": "present"}, InventoryCount=0),
        make_state(ActorStates={}, InventoryCount=0),
    )
    assert verifier.PREDICATES["pickup_not_counted"](trace, params, spec) is True


def t_pickup_false_counted():
    spec = base_spec()
    params = {"pickup": "Pickup1"}
    trace = trace_of(
        make_state(ActorStates={"Pickup1": "present"}, InventoryCount=0),
        make_state(ActorStates={}, InventoryCount=1),
    )
    assert verifier.PREDICATES["pickup_not_counted"](trace, params, spec) is False


def t_pickup_false_never_present():
    spec = base_spec()
    params = {"pickup": "Pickup1"}
    trace = trace_of(make_state(), make_state())
    assert verifier.PREDICATES["pickup_not_counted"](trace, params, spec) is False


# --- run_steps / verify ---

def t_run_steps_trace_shape():
    states = [make_state(), make_state(), make_state(), make_state()]
    fake = FakeUE([states])
    steps = [
        {"action": "move_to", "x": 500, "y": 0},
        {"action": "step", "seconds": 2.0},
        {"action": "interact"},
    ]
    trace = verifier.run_steps(fake, steps)
    assert len(trace) == 4, trace
    assert trace[0] == {"action": None, "state": states[0]}
    assert [e["action"] for e in trace[1:]] == steps
    assert [e["state"] for e in trace] == states
    assert fake.resets == 1


def t_run_steps_uses_step_return_value():
    returned = make_state(StepId=99)
    current = make_state(StepId=3)

    class StepFake(FakeUE):
        def step(self, seconds):
            self.log.append(("step",))
            return returned

        def state(self):
            self.state_calls += 1
            return current

    fake = StepFake([[make_state()]])
    trace = verifier.run_steps(fake, [{"action": "step", "seconds": 1.0}])
    assert trace[1]["state"] == returned
    assert trace[1]["state"] != current


def t_run_steps_all_actions():
    states = [make_state() for _ in range(6)]
    fake = FakeUE([states])
    steps = [
        {"action": "move_to", "x": 1, "y": 2},
        {"action": "jump"},
        {"action": "look_at", "x": 1, "y": 2, "z": 3},
        {"action": "interact"},
        {"action": "step", "seconds": 0.5},
    ]
    trace = verifier.run_steps(fake, steps)
    assert len(trace) == 6
    assert [name for name, *_ in fake.log] == [
        "reset", "move_to", "jump", "look_at", "interact", "step"]


def t_invalid_action_rejected_no_reset():
    fake = FakeUE([[make_state()]])
    try:
        verifier.run_steps(fake, [
            {"action": "move_to", "x": 1, "y": 2},
            {"action": "fly"},
        ])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid action should raise ValueError")
    assert fake.resets == 0, "game must not be touched before validation"
    assert fake.log == []


def t_invalid_action_first_no_reset():
    fake = FakeUE([[make_state()]])
    try:
        verifier.run_steps(fake, [{"action": "teleport"}])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid action should raise ValueError")
    assert fake.resets == 0


def t_malformed_known_action_rejected():
    fake = FakeUE([[make_state()]])
    for bad in ({"action": "move_to", "x": 1},  # missing y
                {"action": "step"},  # missing seconds
                {"action": "look_at", "x": 1, "y": 2}):  # missing z
        try:
            verifier.run_steps(fake, [bad])
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad} should raise ValueError")
    assert fake.resets == 0


def fall_run(dead=True):
    reset = make_state()
    if dead:
        end = make_state(PawnAlive=False, LastZ=-2000,
                         PlayerLocation={"X": 500, "Y": 500, "Z": -2000})
    else:
        end = make_state(PlayerLocation={"X": 500, "Y": 500, "Z": 90})
    return [reset, end]


def t_verify_confirms_3_of_3():
    spec = base_spec()
    fake = FakeUE([fall_run(True), fall_run(True), fall_run(True)])
    result = verifier.verify(fake, [{"action": "step", "seconds": 1.0}],
                             "no_fall_out_of_world", spec)
    assert result == {
        "invariant": "no_fall_out_of_world",
        "confirmed": True,
        "runs": [True, True, True],
        "reason": result["reason"],
    }, result
    assert isinstance(result["reason"], str) and result["reason"]
    assert fake.resets == 3


def t_verify_flaky_2_of_3_not_confirmed():
    spec = base_spec()
    fake = FakeUE([fall_run(True), fall_run(True), fall_run(False)])
    result = verifier.verify(fake, [{"action": "step", "seconds": 1.0}],
                             "no_fall_out_of_world", spec)
    assert result["confirmed"] is False, result
    assert result["runs"] == [True, True, False], result
    assert isinstance(result["reason"], str) and result["reason"]


def t_verify_unknown_invariant_no_replay():
    spec = base_spec()
    fake = FakeUE([[make_state()]])
    result = verifier.verify(fake, [{"action": "step", "seconds": 1.0}],
                             "no_such_bug", spec)
    assert result["confirmed"] is False, result
    assert result["runs"] == [], result
    assert isinstance(result["reason"], str) and result["reason"]
    assert result["invariant"] == "no_such_bug"
    assert fake.resets == 0, "unknown invariant must not replay"


def t_load_spec_file():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec.json")
    spec = verifier.load_spec(path)
    ids = {inv["id"] for inv in spec["invariants"]}
    assert ids == {"no_fall_out_of_world", "door_opens", "pickup_counts"}, ids
    by_id = {inv["id"]: inv for inv in spec["invariants"]}
    assert by_id["door_opens"]["predicate"] == "door_stays_closed_after_interact"
    assert by_id["door_opens"]["params"] == {"door": "Door1", "radius": 150}
    assert by_id["pickup_counts"]["predicate"] == "pickup_not_counted"
    assert by_id["pickup_counts"]["params"] == {"pickup": "Pickup1"}
    assert by_id["no_fall_out_of_world"]["predicate"] == "fell_out_of_world"
    for inv in spec["invariants"]:
        assert isinstance(inv["description"], str) and inv["description"]
    assert spec["intentional"][0]["id"] == "decoy_pit"
    region = spec["intentional"][0]["region"]
    assert region == {"min": {"X": 2350, "Y": 350}, "max": {"X": 2650, "Y": 650}}, region


def main():
    tests = sorted(
        [(name, fn) for name, fn in globals().items()
         if name.startswith("t_") and callable(fn)]
    )
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
