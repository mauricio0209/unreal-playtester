"""Tests for explorer.py with a fake game and a scripted model. Run: python3 agent/test_explorer.py"""

import tempfile
from pathlib import Path

import explorer

SPEC = {"invariants": [{"id": "door_opens", "description": "d", "predicate": "p"},
                       {"id": "pickup_counts", "description": "d", "predicate": "p"}],
        "intentional": []}


def state(alive=True, x=0):
    return {"PlayerLocation": {"X": x, "Y": 0, "Z": 90}, "PawnAlive": alive, "bIsFalling": False,
            "InventoryCount": 0, "KillZ": -1000, "ActorStates": {"Door1": "closed"},
            "ActorLocations": {"Door1": {"X": 3500, "Y": 0, "Z": 150}}}


class FakeUE:
    def __init__(self, tmp, die_on_step=False):
        self.tmp, self.n, self.calls, self.die = Path(tmp), 0, [], die_on_step

    def screenshot(self):
        self.n += 1
        p = self.tmp / f"ue{self.n}.png"
        p.write_bytes(b"\x89PNG fake")
        return p

    def reset(self):
        self.calls.append("reset")
        return state()

    def state(self):
        return state()

    def move_to(self, x, y):
        self.calls.append(("move_to", x, y))

    def interact(self):
        self.calls.append("interact")

    def jump(self):
        self.calls.append("jump")

    def step(self, seconds):
        self.calls.append(("step", seconds))
        return state(alive=not self.die, x=500)


class FakeLLM:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def chat(self, messages):
        self.seen.append(messages)
        return self.replies.pop(0) if self.replies else '{"testing": "door_opens", "action": {"type": "step", "seconds": 1}}'


def run(replies, turns, die=False):
    with tempfile.TemporaryDirectory() as tmp:
        ue, llm = FakeUE(tmp, die), FakeLLM(replies)
        out = explorer.explore(ue, llm, SPEC, Path(tmp) / "shots", max_turns=turns, log=lambda *_: None)
        return out, ue, llm


def t_bug_repro_is_executed_actions():
    out, ue, _ = run([
        '{"thought": "go", "testing": "door_opens", "action": {"type": "move_to", "x": 3440, "y": 0}}',
        'Sure! {"testing": "door_opens", "action": {"type": "step", "seconds": 30}}',  # prose around JSON, clamped seconds
        '{"testing": "door_opens", "action": {"type": "interact"}}',
        '{"testing": "door_opens", "action": {"type": "step", "seconds": 1}}',
        '{"testing": "door_opens", "action": {"type": "jump"}}',  # never stepped: dropped from the repro
        '{"bug": {"invariant": "door_opens", "title": "Door stuck", "hypothesis": "h"}}',
    ], turns=6)
    [h] = out["hypotheses"]
    assert h["steps"] == [{"action": "move_to", "x": 3440, "y": 0},
                          {"action": "step", "seconds": 8.0},
                          {"action": "interact"},
                          {"action": "step", "seconds": 1.0}], h["steps"]
    assert h["before"].name == "t000.png" and h["after"].name == "t006.png"
    assert ue.calls.count("reset") == 2  # initial + after filing
    assert out["actions"] == 6


def t_invalid_replies_are_fed_back_not_executed():
    out, ue, llm = run([
        "no json here",
        '{"testing": "door_opens", "action": {"type": "teleport"}}',
        '{"bug": {"invariant": "door_opens", "title": "t", "hypothesis": "h"}}',  # no step yet
        '{"bug": {"invariant": "made_up", "title": "t", "hypothesis": "h"}}',
    ], turns=4)
    assert out["hypotheses"] == [] and out["actions"] == 0
    assert ue.calls == ["reset"]
    last_user = llm.seen[-1][1]["content"][0]["text"]
    assert "rejected" in last_user, last_user


def t_dead_pawn_only_allows_bug_or_reset():
    out, ue, _ = run([
        '{"testing": "door_opens", "action": {"type": "move_to", "x": 1, "y": 1}}',
        '{"testing": "door_opens", "action": {"type": "step", "seconds": 1}}',
        '{"testing": "door_opens", "action": {"type": "move_to", "x": 2, "y": 2}}',  # rejected: pawn is gone
        '{"testing": "door_opens", "action": {"type": "reset"}}',
    ], turns=4, die=True)
    assert ("move_to", 2, 2) not in ue.calls
    assert ue.calls.count("reset") == 2


def t_action_batches_and_filed_memory():
    out, ue, llm = run([
        '{"testing": "door_opens", "actions": [{"type": "move_to", "x": 3440, "y": 0}, {"type": "step", "seconds": 6},'
        ' {"type": "interact"}, {"type": "step", "seconds": 1}]}',
        '{"bug": {"invariant": "door_opens", "title": "Door stuck", "hypothesis": "h"}}',
        '{"testing": "door_opens", "actions": [{"type": "move_to", "x": 1, "y": 1}, {"type": "reset"}]}',  # reset not alone
        '{"testing": "door_opens", "actions": []}',
    ], turns=4)
    [h] = out["hypotheses"]
    assert [s["action"] for s in h["steps"]] == ["move_to", "step", "interact", "step"]
    assert ("move_to", 1, 1) not in ue.calls
    assert out["actions"] == 5  # 4 batched actions + the bug
    texts = [m[1]["content"][0]["text"] for m in llm.seen]
    assert "Bugs already filed: none" in texts[0]
    assert "door_opens (Door stuck)" in texts[2], texts[2]
    assert "rejected" in texts[3]


def t_vanished_objects_marked_missing():
    s = state()
    s["ActorStates"] = {}
    s["ActorLocations"] = {}
    assert explorer._brief(s, {"Pickup1"})["Objects"] == {"Pickup1": {"state": "missing"}}


def t_screenshot_sent_every_turn():
    _, _, llm = run([], turns=2)
    for msgs in llm.seen:
        img = msgs[1]["content"][1]
        assert img["image_url"]["url"].startswith("data:image/png;base64,"), img


def t_done_ends_and_holding_checks_are_hinted_once():
    spec = {"invariants": [{"id": "moved_east", "description": "d", "predicate": "dsl",
                            "params": {"expr": {"ever": {">": [{"var": "PlayerLocation.X"}, 100]}}}},
                           {"id": "never", "description": "d", "predicate": "dsl",
                            "params": {"expr": False}}], "intentional": []}
    with tempfile.TemporaryDirectory() as tmp:
        ue = FakeUE(tmp)
        llm = FakeLLM(['{"testing": "moved_east", "actions": [{"type": "move_to", "x": 500, "y": 0}, {"type": "step", "seconds": 1}]}',
                       '{"testing": "never", "actions": [{"type": "step", "seconds": 1}]}',
                       '{"thought": "all tested", "done": "both invariants"}',
                       '{"actions": [{"type": "step", "seconds": 1}]}'])
        explorer.explore(ue, llm, spec, Path(tmp) / "shots", max_turns=10, log=lambda *_: None)
    texts = [m[1]["content"][0]["text"] for m in llm.seen]
    assert len(texts) == 3, texts  # "done" stopped the session before the 4th reply
    assert "Automatic check: moved_east holds" in texts[1], texts[1]
    assert "Automatic check" not in texts[2], texts[2]  # hinted once per attempt


def t_done_refused_until_every_invariant_was_tested_and_testing_required():
    one = {"invariants": SPEC["invariants"][:1], "intentional": []}
    with tempfile.TemporaryDirectory() as tmp:
        llm = FakeLLM([
        '{"done": "nothing to do"}',  # door_opens never tested
        '{"actions": [{"type": "step", "seconds": 1}]}',  # no "testing"
        '{"testing": "door_opens", "actions": [{"type": "step", "seconds": 1}]}',
        '{"done": "tested door_opens"}',
        '{"testing": "door_opens", "actions": [{"type": "step", "seconds": 1}]}',
        ])
        explorer.explore(FakeUE(tmp), llm, one, Path(tmp) / "shots", max_turns=6,
                         log=lambda *_: None)
    texts = [m[1]["content"][0]["text"] for m in llm.seen]
    assert len(texts) == 4, texts  # the accepted "done" ended the session
    assert "not done: never tested door_opens" in texts[1], texts[1]
    assert "'testing' must name" in texts[2], texts[2]
    assert "Attempts per invariant: door_opens x1; never tested: none" in texts[3], texts[3]


def t_walk_to_expands_into_replayable_steps():
    out, ue, _ = run([
        '{"testing": "door_opens", "actions": [{"type": "walk_to", "x": 2000, "y": 0}]}',  # fake pawn stops at x=500
        '{"bug": {"invariant": "door_opens", "title": "t", "hypothesis": "h"}}',
    ], turns=2)
    [h] = out["hypotheses"]
    assert h["steps"] == [{"action": "move_to", "x": 2000, "y": 0},
                          {"action": "step", "seconds": 1.0},
                          {"action": "step", "seconds": 1.0}], h["steps"]  # blocked: stopped
    assert out["actions"] == 4, out  # 3 executed + the reset after filing


def t_model_written_fall_rule_probes_the_area_and_sweeps():
    spec = {"invariants": [{"id": "never_die", "description": "d", "predicate": "dsl",
                            "params": {"expr": {"ever": {"==": [{"var": "PawnAlive"}, False]}}}}],
            "intentional": []}

    class Walls(FakeUE):  # the pawn reaches 300 cm in any direction, then a wall stops it
        def move_to(self, x, y):
            super().move_to(x, y)
            self.to = (max(-300, min(300, x)), max(-300, min(300, y)))

        def step(self, seconds):
            self.calls.append(("step", seconds))
            s = state()
            s["PlayerLocation"].update(X=self.to[0], Y=self.to[1])
            return s

    logs = []
    with tempfile.TemporaryDirectory() as tmp:
        ue = Walls(tmp)
        explorer.explore(ue, FakeLLM([]), spec, Path(tmp) / "shots", max_turns=1, log=logs.append)
    assert any("probed walkable area: {'min': {'X': -300, 'Y': -300}, 'max': {'X': 300, 'Y': 300}}"
               in l for l in logs), logs
    lanes = [l for l in logs if l.startswith("sweep lane")]
    assert [l.split(":")[0] for l in lanes] == ["sweep lane y=-300", "sweep lane y=0",
                                                "sweep lane y=300"], lanes


def t_sweep_hands_falls_to_model():
    spec = {"level": {"walkable_area": {"min": {"X": -100, "Y": -300}, "max": {"X": 1100, "Y": 300}}},
            "invariants": [{"id": "no_fall", "description": "d", "predicate": "fell_out_of_world",
                            "params": {"below_z": -200}}], "intentional": []}

    class HoleUE(FakeUE):  # lane y=0 has no floor
        def move_to(self, x, y):
            super().move_to(x, y)
            self.y = y

        def step(self, seconds):
            s = super().step(seconds)
            s["LastZ"] = -500 if self.y == 0 else 90
            return s

    with tempfile.TemporaryDirectory() as tmp:
        ue = HoleUE(tmp)
        llm = FakeLLM(['{"bug": {"invariant": "no_fall", "title": "hole", "hypothesis": "h"}}'])
        out = explorer.explore(ue, llm, spec, Path(tmp) / "shots", max_turns=1, log=lambda *_: None)
    [h] = out["hypotheses"]
    assert h["steps"] == [{"action": "move_to", "x": 0, "y": 0},
                          {"action": "step", "seconds": 2.0}], h["steps"]
    assert len(llm.seen) == 1  # the model was only asked once, about the fall
    assert "sweep stopped" in llm.seen[0][1]["content"][0]["text"]
    lanes = [c[2] for c in ue.calls if c[0] == "move_to" and c[1] == 0]
    assert lanes == [-200, 0], lanes  # lane y=200 still pending when turns ran out


def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
