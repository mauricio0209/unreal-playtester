"""Tests for checks.py using hand-made traces. Run: python3 agent/test_checks.py"""

import checks
import verifier


def make_state(**overrides):
    state = {
        "PawnAlive": True,
        "PlayerLocation": {"X": 0, "Y": 0, "Z": 100},
        "LastZ": 100,
        "KillZ": -1000,
        "InventoryCount": 0,
        "ActorStates": {},
        "ActorLocations": {},
    }
    state.update(overrides)
    return state


def trace_of(*states, actions=None):
    entries = [{"action": None, "state": states[0]}]
    for i, state in enumerate(states[1:]):
        action = {"action": "step", "seconds": 1.0}
        if actions is not None:
            action = actions[i]
        entries.append({"action": action, "state": state})
    return entries


def check_of(violation, check_id="some_rule"):
    return {
        "id": check_id,
        "description": "a design rule",
        "violation": violation,
    }


GATE_VIOLATION = {
    "ever": {
        "and": [
            {"==": [{"var": "ActorStates.IronGate"}, "open"]},
            {"==": [{"var": "ActorStates.IronKey"}, "present"]},
        ]
    }
}

APPLE_VIOLATION = {
    "ever": {
        "and": [
            {"==": [{"prev": "ActorStates.Apple"}, "present"]},
            {"==": [{"var": "ActorStates.Apple"}, None]},
            {"!=": [{"-": [{"var": "InventoryCount"}, {"prev": "InventoryCount"}]}, 1]},
        ]
    }
}


def t_literal_truthiness():
    trace = trace_of(make_state())
    assert checks.evaluate(trace, True) is True
    assert checks.evaluate(trace, False) is False
    assert checks.evaluate(trace, None) is False
    assert checks.evaluate(trace, 1) is True
    assert checks.evaluate(trace, 0) is False
    assert checks.evaluate(trace, "x") is True
    assert checks.evaluate(trace, "") is False


def t_var_reads_current_state():
    trace = trace_of(
        make_state(ActorStates={"Door": "closed"}),
        make_state(ActorStates={"Door": "open"}),
    )
    assert checks.evaluate(trace, {"==": [{"var": "ActorStates.Door"}, "open"]}) is True
    assert checks.evaluate(trace, {"==": [{"var": "ActorStates.Door"}, "closed"]}) is False


def t_var_missing_key_is_null():
    trace = trace_of(make_state())
    assert checks.evaluate(trace, {"==": [{"var": "ActorStates.Nope"}, None]}) is True
    assert checks.evaluate(trace, {"var": "ActorStates.Nope"}) is False


def t_prev_at_first_state_is_null():
    trace = trace_of(make_state(InventoryCount=7))
    assert checks.evaluate(trace, {"==": [{"prev": "InventoryCount"}, None]}) is True
    assert checks.evaluate(trace, {"prev": "InventoryCount"}) is False


def t_prev_reads_previous_state():
    trace = trace_of(
        make_state(InventoryCount=2),
        make_state(InventoryCount=5),
    )
    assert checks.evaluate(trace, {"==": [{"prev": "InventoryCount"}, 2]}) is True
    assert checks.evaluate(trace, {"==": [{"var": "InventoryCount"}, 5]}) is True


def t_first_at_first_state():
    trace = trace_of(make_state(InventoryCount=7))
    expr = {"==": [{"first": "InventoryCount"}, {"var": "InventoryCount"}]}
    assert checks.evaluate(trace, expr) is True


def t_first_stays_at_first_state():
    trace = trace_of(
        make_state(InventoryCount=2),
        make_state(InventoryCount=9),
    )
    assert checks.evaluate(trace, {"==": [{"first": "InventoryCount"}, 2]}) is True
    assert checks.evaluate(trace, {"==": [{"first": "InventoryCount"}, 9]}) is False


def t_did_matches_producing_action():
    trace = trace_of(
        make_state(),
        make_state(),
        make_state(),
        actions=[{"action": "interact"}, {"action": "step", "seconds": 1.0}],
    )
    assert checks.evaluate(trace, {"did": "step"}) is True
    assert checks.evaluate(trace, {"did": "interact"}) is False
    assert checks.evaluate(trace, {"ever": {"did": "interact"}}) is True
    assert checks.evaluate(trace, {"ever": {"did": "jump"}}) is False


def t_did_at_first_state_is_false():
    trace = trace_of(make_state())
    for name in ("move_to", "look_at", "jump", "interact", "step"):
        assert checks.evaluate(trace, {"did": name}) is False


def t_dist_between_locations():
    trace = trace_of(
        make_state(
            PlayerLocation={"X": 0, "Y": 0, "Z": 0},
            ActorLocations={"Gate": {"X": 3, "Y": 4, "Z": 0}},
        )
    )
    expr = {"dist": ["PlayerLocation", "ActorLocations.Gate"]}
    assert checks.evaluate(trace, {"==": [expr, 5.0]}) is True


def t_dist_missing_is_null():
    trace = trace_of(make_state())
    expr = {"dist": ["PlayerLocation", "ActorLocations.Gate"]}
    assert checks.evaluate(trace, {"==": [expr, None]}) is True
    assert checks.evaluate(trace, expr) is False


def t_dist_wrong_types_is_null():
    trace = trace_of(
        make_state(
            PlayerLocation={"X": "far", "Y": 0, "Z": 0},
            ActorLocations={"Gate": {"X": 3, "Y": 4, "Z": 0}},
        )
    )
    expr = {"dist": ["PlayerLocation", "ActorLocations.Gate"]}
    assert checks.evaluate(trace, {"==": [expr, None]}) is True


def t_comparison_operators():
    trace = trace_of(make_state())
    assert checks.evaluate(trace, {"==": [1, 1]}) is True
    assert checks.evaluate(trace, {"==": [1, 1.0]}) is True
    assert checks.evaluate(trace, {"==": [1, 2]}) is False
    assert checks.evaluate(trace, {"==": ["a", "a"]}) is True
    assert checks.evaluate(trace, {"==": [True, True]}) is True
    assert checks.evaluate(trace, {"==": [True, 1]}) is False
    assert checks.evaluate(trace, {"==": [None, None]}) is True
    assert checks.evaluate(trace, {"==": [None, 0]}) is False
    assert checks.evaluate(trace, {"!=": [1, 2]}) is True
    assert checks.evaluate(trace, {"!=": [1, 1]}) is False
    assert checks.evaluate(trace, {"<": [1, 2]}) is True
    assert checks.evaluate(trace, {"<=": [2, 2]}) is True
    assert checks.evaluate(trace, {">": [2, 1]}) is True
    assert checks.evaluate(trace, {">=": [1, 2]}) is False


def t_ordering_with_non_number_is_false():
    trace = trace_of(make_state())
    for op in ("<", "<=", ">", ">="):
        assert checks.evaluate(trace, {op: ["a", "b"]}) is False
        assert checks.evaluate(trace, {op: [None, 1]}) is False
        assert checks.evaluate(trace, {op: [True, 1]}) is False
        assert checks.evaluate(trace, {op: [1, None]}) is False


def t_arithmetic_operators():
    trace = trace_of(make_state())
    assert checks.evaluate(trace, {"==": [{"+": [2, 3]}, 5]}) is True
    assert checks.evaluate(trace, {"==": [{"-": [5, 8]}, -3]}) is True
    assert checks.evaluate(trace, {"==": [{"+": ["a", 1]}, None]}) is True
    assert checks.evaluate(trace, {"==": [{"-": [None, 1]}, None]}) is True
    assert checks.evaluate(trace, {"==": [{"+": [True, 1]}, None]}) is True


def t_logic_operators():
    trace = trace_of(make_state())
    assert checks.evaluate(trace, {"and": [True, True]}) is True
    assert checks.evaluate(trace, {"and": [True, False]}) is False
    assert checks.evaluate(trace, {"or": [False, False]}) is False
    assert checks.evaluate(trace, {"or": [False, True]}) is True
    assert checks.evaluate(trace, {"not": False}) is True
    assert checks.evaluate(trace, {"not": True}) is False
    assert checks.evaluate(trace, {"not": None}) is True
    assert checks.evaluate(trace, {"and": [1, "x"]}) is True
    assert checks.evaluate(trace, {"and": [1, None]}) is False


def t_ever_always_final():
    good = make_state(ActorStates={"D": "open"})
    bad = make_state(ActorStates={"D": "closed"})
    expr = {"==": [{"var": "ActorStates.D"}, "open"]}
    assert checks.evaluate(trace_of(bad, good), {"ever": expr}) is True
    assert checks.evaluate(trace_of(bad, bad), {"ever": expr}) is False
    assert checks.evaluate(trace_of(good, good), {"always": expr}) is True
    assert checks.evaluate(trace_of(good, bad), {"always": expr}) is False
    assert checks.evaluate(trace_of(bad, good), {"final": expr}) is True
    assert checks.evaluate(trace_of(good, bad), {"final": expr}) is False


def t_after_holds():
    before = make_state(ActorStates={"D": "open"})
    after = make_state(ActorStates={"D": "closed"})
    expr = {
        "after": [
            {"==": [{"var": "ActorStates.D"}, "open"]},
            {"==": [{"var": "ActorStates.D"}, "closed"]},
        ]
    }
    assert checks.evaluate(trace_of(before, after), expr) is True
    # Same-state only at the end is not enough: last must be strictly later.
    assert checks.evaluate(trace_of(after, after), expr) is False
    # b false at the last state.
    assert checks.evaluate(trace_of(before, before), expr) is False


def t_after_single_state_is_false():
    trace = trace_of(make_state(ActorStates={"D": "open"}))
    expr = {
        "after": [
            {"==": [{"var": "ActorStates.D"}, "open"]},
            {"==": [{"var": "ActorStates.D"}, "open"]},
        ]
    }
    assert checks.evaluate(trace, expr) is False


def t_after_needs_strictly_later_index():
    first_open = make_state(ActorStates={"D": "open"})
    last_open = make_state(ActorStates={"D": "open"})
    expr = {
        "after": [
            {"==": [{"var": "ActorStates.D"}, "open"]},
            {"==": [{"var": "ActorStates.D"}, "open"]},
        ]
    }
    assert checks.evaluate(trace_of(first_open, last_open), expr) is True
    assert checks.evaluate(trace_of(first_open), expr) is False


def t_null_handling_never_raises():
    trace = trace_of(
        make_state(PlayerLocation="nowhere", ActorStates=None),
        make_state(PlayerLocation=None, InventoryCount="many"),
    )
    probes = [
        {"var": "PlayerLocation.X"},
        {"var": "ActorStates.Door"},
        {"prev": "ActorStates.Door"},
        {"first": "Nope.Nested.Deep"},
        {"==": [{"var": "PlayerLocation"}, None]},
        {"<": [{"var": "InventoryCount"}, 5]},
        {"+": [{"var": "InventoryCount"}, 1]},
        {"-": [{"prev": "InventoryCount"}, {"var": "InventoryCount"}]},
        {"dist": ["PlayerLocation", "ActorLocations.Gate"]},
        {"and": [{"var": "ActorStates.Door"}, False]},
        {"not": {"var": "Missing.Key"}},
        {"ever": {"==": [{"var": "Missing"}, None]}},
        {"after": [{"var": "Missing"}, {"var": "Missing"}]},
    ]
    for expr in probes:
        assert isinstance(checks.evaluate(trace, expr), bool)


def t_example_gate_violation_true():
    trace = trace_of(
        make_state(ActorStates={"IronGate": "closed", "IronKey": "present"}),
        make_state(ActorStates={"IronGate": "open", "IronKey": "present"}),
    )
    assert checks.evaluate(trace, GATE_VIOLATION) is True


def t_example_gate_violation_false():
    trace = trace_of(
        make_state(ActorStates={"IronGate": "closed", "IronKey": "present"}),
        make_state(ActorStates={"IronGate": "open"}),
    )
    assert checks.evaluate(trace, GATE_VIOLATION) is False
    shut = trace_of(
        make_state(ActorStates={"IronGate": "closed", "IronKey": "present"}),
        make_state(ActorStates={"IronGate": "closed", "IronKey": "present"}),
    )
    assert checks.evaluate(shut, GATE_VIOLATION) is False


def t_example_apple_violation_true():
    trace = trace_of(
        make_state(ActorStates={"Apple": "present"}, InventoryCount=0),
        make_state(ActorStates={}, InventoryCount=0),
    )
    assert checks.evaluate(trace, APPLE_VIOLATION) is True


def t_example_apple_violation_false():
    trace = trace_of(
        make_state(ActorStates={"Apple": "present"}, InventoryCount=0),
        make_state(ActorStates={}, InventoryCount=1),
    )
    assert checks.evaluate(trace, APPLE_VIOLATION) is False
    never = trace_of(
        make_state(ActorStates={}, InventoryCount=0),
        make_state(ActorStates={}, InventoryCount=0),
    )
    assert checks.evaluate(never, APPLE_VIOLATION) is False


def t_validate_accepts_valid_check():
    checks.validate(check_of(GATE_VIOLATION, "gate_needs_key"))
    checks.validate(check_of(APPLE_VIOLATION, "apple_worth_one"))
    checks.validate(check_of(True, "ok_lit"))
    checks.validate(check_of({"did": "step"}, "ok_did"))
    checks.validate(check_of({"dist": ["PlayerLocation", "ActorLocations.G"]}, "ok_dist"))


def t_validate_unknown_operator():
    for bad in ({"nope": [1, 2]}, {"EVERY": True}, {"Var": "X"}):
        try:
            checks.validate(check_of(bad))
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad} should raise ValueError")


def t_validate_bad_paths():
    for bad_path in ("", ".a", "a..b", "a b", "a-b", "a.", 123, None, ["X"]):
        for op in ("var", "prev", "first"):
            try:
                checks.validate(check_of({op: bad_path}))
            except ValueError:
                pass
            else:
                raise AssertionError(f"{op}:{bad_path!r} should raise ValueError")
    try:
        checks.validate(check_of({"dist": ["PlayerLocation", "bad path"]}))
    except ValueError:
        pass
    else:
        raise AssertionError("bad dist path should raise ValueError")
    try:
        checks.validate(check_of({"dist": ["PlayerLocation"]}))
    except ValueError:
        pass
    else:
        raise AssertionError("short dist should raise ValueError")


def t_validate_two_key_dicts():
    bad = {"==": [1, 1], "!=": [1, 2]}
    try:
        checks.validate(check_of(bad))
    except ValueError:
        pass
    else:
        raise AssertionError("two-key dict should raise ValueError")
    try:
        checks.validate(check_of({}))
    except ValueError:
        pass
    else:
        raise AssertionError("empty dict should raise ValueError")


def t_validate_too_deep():
    deep = True
    for _ in range(13):
        deep = {"not": deep}
    try:
        checks.validate(check_of(deep))
    except ValueError:
        pass
    else:
        raise AssertionError("too-deep expression should raise ValueError")


def t_validate_deep_boundary_ok():
    deep = True
    for _ in range(11):
        deep = {"not": deep}
    checks.validate(check_of(deep))


def t_validate_too_large():
    big = {"and": [True] * 201}
    try:
        checks.validate(check_of(big))
    except ValueError:
        pass
    else:
        raise AssertionError("too-large expression should raise ValueError")


def t_validate_bad_ids():
    for bad_id in ("", "Abc", "0abc", "has-dash", "has space", "A" * 65, 123, None):
        bad = {"id": bad_id, "description": "d", "violation": True}
        try:
            checks.validate(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"id {bad_id!r} should raise ValueError")


def t_validate_bad_check_shape():
    for bad in (
        {"id": "x", "description": "d"},
        {"id": "x", "description": "d", "violation": True, "extra": 1},
        {"id": "x", "violation": True},
        [],
        "nope",
        None,
    ):
        try:
            checks.validate(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad!r} should raise ValueError")


def t_validate_bad_description():
    for bad_desc in ("", "x" * 501, 123, None):
        try:
            checks.validate(check_of(True, "ok"))
        except ValueError:  # pragma: no cover - sanity, valid check passes
            raise AssertionError("valid check should not raise")
        try:
            checks.validate({"id": "ok", "description": bad_desc, "violation": True})
        except ValueError:
            pass
        else:
            raise AssertionError(f"description {bad_desc!r} should raise ValueError")


def t_validate_bad_literals_and_shapes():
    for bad in ([1, 2], "x" * 201, {"did": "fly"}, {"and": []}, {"not": [True]},
                {"after": [True]}, {"==": [True]}, {"==": [True, False, True]}):
        try:
            checks.validate(check_of(bad))
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad!r} should raise ValueError")


class FakeUE:
    """Scripted ue double. Each run is a list of states, one per trace entry."""

    def __init__(self, runs):
        self._runs = runs
        self.resets = 0

    def reset(self):
        self.resets += 1
        index = min(self.resets - 1, len(self._runs) - 1)
        self._states = self._runs[index]
        self._i = 0
        return self._states[0]

    def _advance(self):
        if self._i + 1 < len(self._states):
            self._i += 1
        return self._states[self._i]

    def step(self, seconds):
        return self._advance()

    def move_to(self, x, y):
        return self._advance()

    def jump(self):
        return self._advance()

    def look_at(self, x, y, z):
        return self._advance()

    def interact(self):
        return self._advance()

    def state(self):
        return self._states[self._i]


def dsl_spec(expr):
    return {
        "invariants": [
            {"id": "gate_rule", "description": "gate stays locked",
             "predicate": "dsl", "params": {"expr": expr}},
        ],
        "intentional": [],
    }


def t_dsl_violation_predicate():
    trace = trace_of(
        make_state(ActorStates={"IronGate": "closed", "IronKey": "present"}),
        make_state(ActorStates={"IronGate": "open", "IronKey": "present"}),
    )
    assert verifier.PREDICATES["dsl"](trace, {"expr": GATE_VIOLATION}, {}) is True
    assert checks.dsl_violation(trace, {"expr": GATE_VIOLATION}, {}) is True


def t_verify_dsl_confirms():
    reset = make_state(ActorStates={"IronGate": "closed", "IronKey": "present"})
    end = make_state(ActorStates={"IronGate": "open", "IronKey": "present"})
    fake = FakeUE([[reset, end], [reset, end]])
    result = verifier.verify(fake, [{"action": "step", "seconds": 1.0}],
                             "gate_rule", dsl_spec(GATE_VIOLATION), runs=2)
    assert result["confirmed"] is True, result
    assert result["runs"] == [True, True], result
    assert result["invariant"] == "gate_rule"
    assert isinstance(result["reason"], str) and result["reason"]


def t_verify_dsl_not_confirmed():
    reset = make_state(ActorStates={"IronGate": "closed", "IronKey": "present"})
    end = make_state(ActorStates={"IronGate": "open"})
    fake = FakeUE([[reset, end]])
    result = verifier.verify(fake, [{"action": "step", "seconds": 1.0}],
                             "gate_rule", dsl_spec(GATE_VIOLATION), runs=1)
    assert result["confirmed"] is False, result
    assert result["runs"] == [False], result


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
