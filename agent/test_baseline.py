"""Tests for baseline.py with a fake game. Run: python3 agent/test_baseline.py"""

import copy
import tempfile
from pathlib import Path

import baseline

DOOR_SPEC = {"invariants": [{"id": "door_opens",
                             "description": "d",
                             "predicate": "door_stays_closed_after_interact",
                             "params": {"door": "Door1", "radius": 150}}],
             "intentional": []}


def door_state():
    return {"PlayerLocation": {"X": 0, "Y": 0, "Z": 90},
            "PawnAlive": True, "bIsFalling": False,
            "InventoryCount": 0, "KillZ": -1000,
            "ActorStates": {"Door1": "closed"},
            "ActorLocations": {"Door1": {"X": 300, "Y": 0, "Z": 150}}}


def fall_spec(lanes_y_max=300, intentional=None):
    return {"level": {"walkable_area": {"min": {"X": 0, "Y": 0},
                                        "max": {"X": 600, "Y": lanes_y_max}}},
            "invariants": [{"id": "no_fall", "description": "d",
                            "predicate": "fell_out_of_world",
                            "params": {"below_z": -200}}],
            "intentional": intentional or []}


def lane_state():
    return {"PlayerLocation": {"X": 100, "Y": 100, "Z": 90},
            "PawnAlive": True, "bIsFalling": False,
            "InventoryCount": 0, "KillZ": -1000, "LastZ": 90,
            "ActorStates": {}, "ActorLocations": {}}


class FakeUE:
    def __init__(self, tmp, reset_state, step_fn=None):
        self.tmp, self.n, self.calls = Path(tmp), 0, []
        self._reset_state = reset_state
        self._step_fn = step_fn
        self.state_now = None
        self.target = None

    def screenshot(self):
        self.n += 1
        p = self.tmp / f"ue{self.n}.png"
        p.write_bytes(b"\x89PNG fake")
        return p

    def reset(self):
        self.calls.append("reset")
        self.state_now = copy.deepcopy(self._reset_state)
        self.target = None
        return self.state_now

    def state(self):
        return self.state_now

    def move_to(self, x, y):
        self.calls.append(("move_to", x, y))
        self.target = (x, y)

    def interact(self):
        self.calls.append("interact")

    def jump(self):
        self.calls.append("jump")

    def look_at(self, x, y, z):
        self.calls.append(("look_at", x, y, z))

    def step(self, seconds):
        self.calls.append(("step", seconds))
        if self._step_fn is not None:
            self._step_fn(self, seconds)
        return self.state_now


def teleport(ue, _seconds):
    if ue.target is not None:
        ue.state_now["PlayerLocation"] = {"X": ue.target[0],
                                          "Y": ue.target[1], "Z": 90}


def fall_at(floor):
    def fell(ue, seconds):
        teleport(ue, seconds)
        ue.state_now["PawnAlive"] = False
        ue.state_now["LastZ"] = -2000
        ue.state_now["LastFloorLocation"] = dict(floor)
    return fell


def run(make_ue, spec, **kwargs):
    with tempfile.TemporaryDirectory() as tmp:
        ue = make_ue(tmp)
        logs = []
        out = baseline.explore(ue, None, spec, Path(tmp) / "shots",
                               log=logs.append, **kwargs)
        shots = sorted((Path(tmp) / "shots").glob("*.png"))
        return out, ue, logs, shots


def t_door_episode_files_first_hold():
    with tempfile.TemporaryDirectory() as tmp:
        ue = FakeUE(tmp, door_state(), teleport)
        logs = []
        out = baseline.explore(ue, None, DOOR_SPEC, Path(tmp) / "shots",
                               log=logs.append)
        shots = sorted((Path(tmp) / "shots").glob("*.png"))
        assert len(out["hypotheses"]) == 1, out["hypotheses"]
        [h] = out["hypotheses"]
        assert h["invariant"] == "door_opens", h
        assert h["title"] == "door_opens broken (scripted check)", h
        assert h["hypothesis"], h
        # move_to, one travel step (300cm/600 + 1s = 1.5s), interact, then
        # the first trailing step is where the predicate first holds; the
        # second trailing step ran but is not part of the repro.
        assert h["steps"] == [{"action": "move_to", "x": 300, "y": 0},
                              {"action": "step", "seconds": 1.5},
                              {"action": "interact"},
                              {"action": "step", "seconds": 1.0}], h["steps"]
        assert out["actions"] == 5, out  # episode ran to the end
        assert Path(h["before"]).is_file() and Path(h["after"]).is_file()
        assert len(shots) == 2, shots
        assert any("object Door1" in line for line in logs), logs
        assert any("door_opens" in line for line in logs), logs


def t_fall_during_lane_files_fall():
    out, ue, logs, _ = run(
        lambda tmp: FakeUE(tmp, lane_state(), fall_at({"X": 100, "Y": 100})),
        fall_spec())
    assert len(out["hypotheses"]) == 1, out["hypotheses"]
    [h] = out["hypotheses"]
    assert h["invariant"] == "no_fall", h
    assert h["steps"] and h["steps"][-1]["action"] == "step", h["steps"]


def t_fall_in_intentional_region_is_quiet():
    spec = fall_spec(intentional=[{"region": {"min": {"X": 0, "Y": 0},
                                              "max": {"X": 1000, "Y": 1000}}}])
    out, ue, logs, _ = run(
        lambda tmp: FakeUE(tmp, lane_state(), fall_at({"X": 100, "Y": 100})),
        spec)
    assert out["hypotheses"] == [], out["hypotheses"]
    assert out["actions"] > 0, out  # the lane still ran


def t_invariant_filed_once():
    # Two lanes, both fall outside any intentional region: one hypothesis.
    out, ue, logs, _ = run(
        lambda tmp: FakeUE(tmp, lane_state(), fall_at({"X": 100, "Y": 100})),
        fall_spec(lanes_y_max=500))
    assert len(out["hypotheses"]) == 1, out["hypotheses"]
    assert out["hypotheses"][0]["invariant"] == "no_fall"


def t_deadline_stops_new_episodes():
    import time as time_mod
    state = door_state()
    state["ActorStates"] = {"B_obj": "closed", "A_obj": "closed"}
    state["ActorLocations"] = {"B_obj": {"X": 600, "Y": 0, "Z": 150},
                               "A_obj": {"X": 1200, "Y": 0, "Z": 150}}
    spec = {"invariants": [{"id": "x", "predicate": "unknown_pred"}],
            "intentional": []}
    real = time_mod.monotonic
    ticks = iter([0, 0, 999])
    time_mod.monotonic = lambda: next(ticks, 999)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            ue = FakeUE(tmp, state, teleport)
            out = baseline.explore(ue, None, spec, Path(tmp) / "shots",
                                   deadline_s=360.0, log=lambda *_: None)
    finally:
        time_mod.monotonic = real
    moves = [c for c in ue.calls if c[0] == "move_to"]
    assert moves == [("move_to", 1200, 0)], moves  # sorted first object only
    assert out["hypotheses"] == [] and out["actions"] == 5, out


def t_zero_deadline_runs_nothing():
    out, ue, logs, shots = run(
        lambda tmp: FakeUE(tmp, door_state(), teleport),
        DOOR_SPEC, deadline_s=0)
    assert out == {"hypotheses": [], "actions": 0}, out
    assert shots == [], shots


def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
