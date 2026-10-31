"""Tests for oracle.py with a scripted model. Run: python3 agent/test_oracle.py"""

import json
from pathlib import Path

import oracle

DESIGN = "The iron gate stays locked until the iron key is picked up."
STATE = {"PawnAlive": True, "PlayerLocation": {"X": 0, "Y": 0, "Z": 90},
         "InventoryCount": 0, "KillZ": -1000,
         "ActorStates": {"IronGate": "closed", "IronKey": "present"},
         "ActorLocations": {"IronGate": {"X": 100, "Y": 0, "Z": 50}}}


def check(cid, violation=None):
    return {"id": cid, "description": f"the design rule for {cid}",
            "violation": violation if violation is not None else {"ever": True}}


def payload(*cids):
    return json.dumps({"checks": [check(c) for c in cids]})


class FakeLLM:
    def __init__(self, replies):
        self.replies, self.seen, self.tokens = list(replies), [], []

    def chat(self, messages, max_tokens=4000):
        self.seen.append(list(messages))
        self.tokens.append(max_tokens)
        return self.replies.pop(0) if self.replies else "no more replies"


def accept_all(check):
    return None


def reject(*bad, msg="bad expr"):
    def validate(check):
        if check["id"] in bad:
            raise ValueError(msg)
        return None
    return validate


def run(replies, validate=accept_all, attempts=3):
    llm, logs = FakeLLM(replies), []
    out = oracle.write_checks(llm, DESIGN, STATE, log=logs.append,
                              attempts=attempts, validate=validate)
    return out, llm, logs


def t_valid_checks_first_reply():
    out, llm, logs = run([payload("a", "b")])
    assert [c["id"] for c in out] == ["a", "b"]
    assert len(llm.seen) == 1 and sum(l.startswith("attempt") for l in logs) == 1
    assert llm.tokens == [8000]


def t_prose_around_json():
    reply = "Here you go:\n" + payload("a") + "\nHope this helps!"
    out, llm, _ = run([reply])
    assert [c["id"] for c in out] == ["a"]


def t_invalid_check_retried_with_feedback():
    out, llm, logs = run(
        [payload("good", "bad"), payload("good", "fixed")],
        validate=reject("bad", msg="unknown operator 'whenever'"))
    assert [c["id"] for c in out] == ["good", "fixed"]
    assert len(llm.seen) == 2 and sum(l.startswith("attempt") for l in logs) == 2
    assert any("rejected bad: unknown operator" in l for l in logs), logs
    feedback = llm.seen[1][-1]["content"]
    assert "bad" in feedback and "unknown operator 'whenever'" in feedback, feedback
    assert llm.seen[1][-2]["content"] == payload("good", "bad")  # reply kept


def t_worse_retry_keeps_better_result():
    out, llm, _ = run(
        [payload("a", "b", "c"), payload("a")],
        validate=reject("c", msg="boom"), attempts=3)
    assert [c["id"] for c in out] == ["a", "b"], out


def t_one_check_per_line_isolates_a_bad_bracket():
    good = json.dumps(check("good"))
    broken = json.dumps(check("broken"))[:-1]  # the model dropped a closing brace
    out, llm, _ = run([f"{good}\n{broken}", f"{good}\n{json.dumps(check('broken'))}"])
    assert [c["id"] for c in out] == ["good", "broken"], out
    feedback = llm.seen[1][-1]["content"]
    assert "line 2" in feedback and "invalid JSON" in feedback, feedback


def t_unparseable_until_attempts_out_raises():
    llm, logs = FakeLLM(["no json here", "still { not json", "{oops"]), []
    try:
        oracle.write_checks(llm, DESIGN, STATE, log=logs.append,
                            attempts=3, validate=accept_all)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    assert len(llm.seen) == 3 and sum(l.startswith("attempt") for l in logs) == 3


def t_duplicate_ids_first_wins():
    dup = json.dumps({"checks": [check("a", {"ever": True}),
                                 check("a", {"ever": False}),
                                 check("b")]})
    out, llm, _ = run([dup])
    assert [c["id"] for c in out] == ["a", "b"]
    assert out[0]["violation"] == {"ever": True}
    assert len(llm.seen) == 1  # duplicates are not a retry


def t_to_spec_without_base():
    spec = oracle.to_spec([check("a")])
    assert spec == {"intentional": [],
                    "invariants": [{"id": "a", "description": "the design rule for a",
                                    "predicate": "dsl",
                                    "params": {"expr": {"ever": True}}}]}
    assert "level" not in spec


def t_to_spec_with_base():
    base = {"level": {"name": "L1"}, "intentional": [{"region": "r"}]}
    spec = oracle.to_spec([check("a", {"final": True})], base=base)
    assert spec["level"] == {"name": "L1"}
    assert spec["intentional"] == [{"region": "r"}]
    [inv] = spec["invariants"]
    assert inv["predicate"] == "dsl" and inv["params"] == {"expr": {"final": True}}


def t_system_prompt_contains_reference():
    _, llm, _ = run([payload("a")])
    system = llm.seen[0][0]["content"]
    assert llm.seen[0][0]["role"] == "system"
    ref = (Path(oracle.__file__).resolve().parent
           / "checks_reference.md").read_text(encoding="utf-8")
    assert ref in system
    user = llm.seen[0][1]["content"]
    assert DESIGN in user and json.dumps(STATE) in user


def t_guard_rejects_unknown_paths_and_checks_firing_at_load():
    state = {"InventoryCount": 0, "PlayerLocation": {"X": 0, "Y": 0, "Z": 90},
             "ActorStates": {"Gate": "closed", "Gem": "present"},
             "ActorLocations": {"Gate": {"X": 1, "Y": 2, "Z": 3}}}
    ok = check("gem_counted", {"ever": {"and": [{"==": [{"prev": "ActorStates.Gem"}, "present"]},
                                                {"==": [{"var": "ActorStates.Gem"}, None]}]}})
    oracle.guard(ok, state)
    oracle.guard(check("near", {"<": [{"dist": ["PlayerLocation", "ActorLocations.Gate"]}, 1]}), state)
    for bad, words in ((check("typo", {"!=": [{"var": "ActorStates.Gaet"}, "closed"]}), "Gaet"),
                       (check("loc", {"<": [{"dist": ["PlayerLocation", "ActorLocations.Gem"]}, 9]}),
                        "ActorLocations.Gem"),
                       (check("at_load", {"ever": {"==": [{"var": "ActorStates.Gate"}, "closed"]}}),
                        "fresh level load"),
                       (check("idle", {"ever": {"==": [{"prev": "ActorStates.Gem"}, "present"]}}),
                        "only waits"),
                       (dict(check("terse", {"==": [{"var": "ActorStates.Gate"}, "open"]}),
                             description="d"), "design rule")):
        try:
            oracle.guard(bad, state)
        except ValueError as exc:
            assert words in str(exc), exc
        else:
            raise AssertionError(f"{bad['id']} should be rejected")


def t_default_validator_applies_the_guard():
    state = {"ActorStates": {"Gate": "closed"}}
    llm = FakeLLM([json.dumps(check("typo", {"==": [{"var": "ActorStates.Gaet"}, "open"]})) + "\n" +
                   json.dumps(check("ok", {"==": [{"var": "ActorStates.Gate"}, "open"]}))])
    out = oracle.write_checks(llm, DESIGN, state, log=lambda *_: None, attempts=1)
    assert [c["id"] for c in out] == ["ok"], out


def t_uncovered_objects_trigger_one_review():
    state = {"ActorStates": {"Gate": "closed", "Key": "present"}}
    gate = check("gate", {"==": [{"var": "ActorStates.Gate"}, "open"]})
    key = check("key", {"==": [{"var": "ActorStates.Key"}, "gone"]})
    logs = []
    llm = FakeLLM(["1. " + json.dumps(gate), json.dumps(gate) + "\n- " + json.dumps(key)])
    out = oracle.write_checks(llm, DESIGN, state, log=logs.append)
    assert [c["id"] for c in out] == ["gate", "key"], out
    assert "No check reads these objects: Key" in llm.seen[1][-1]["content"]
    # still half uncovered after every attempt: accepted (the document may say nothing about it)
    llm = FakeLLM([json.dumps(gate)] * 3)
    out = oracle.write_checks(llm, DESIGN, state, log=lambda *_: None)
    assert [c["id"] for c in out] == ["gate"] and len(llm.seen) == 3, (out, len(llm.seen))
    # most objects never read: a clear failure instead of a session with no oracle
    big = {"ActorStates": {"Gate": "closed", "Key": "present", "Coin": "present"}}
    try:
        oracle.write_checks(FakeLLM([json.dumps(gate)] * 3), DESIGN, big, log=lambda *_: None)
    except ValueError as exc:
        assert "read only 1 of 3 objects" in str(exc), exc
    else:
        raise AssertionError("one check over three objects must fail")


def t_rule_sentences_and_one_review():
    doc = ("# Notes\nThe gate opens with a key. Torches light the hall.\n\n"
           "- a coin is worth 1,\n- the floor must never break.\n")
    assert oracle.rule_sentences(doc) == ["- a coin is worth 1,", "the floor must never break."], \
        oracle.rule_sentences(doc)
    state = {"ActorStates": {"Coin": "present"}, "PawnAlive": True}
    coin = check("coin_worth", {"ever": {"==": [{"var": "ActorStates.Coin"}, "gone"]}})
    floor = check("floor_holds", {"ever": {"==": [{"var": "PawnAlive"}, False]}})
    llm = FakeLLM([json.dumps(coin), json.dumps(coin) + "\n" + json.dumps(floor)])
    out = oracle.write_checks(llm, doc, state, log=lambda *_: None)
    assert [c["id"] for c in out] == ["coin_worth", "floor_holds"], out
    review = llm.seen[1][-1]["content"]
    assert "2. the floor must never break." in review and "Torches" not in review, review


def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
