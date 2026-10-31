# Task: the model writes a level's checks from its design document (`agent/oracle.py`)

Create `agent/oracle.py` and `agent/test_oracle.py`. Python 3.14, standard library only. Do
not modify any other file. Run every `agent/test_*.py` and make sure all pass before
finishing.

## Why

Instead of a human writing a predicate for every rule of a game, Muse Spark reads the game's
design document (plain English) and writes the checks itself, in the JSON check language
specified in `agent/checks_reference.md` (**read it first**). A separate deterministic module
`agent/checks.py` (being written in parallel; it will expose `validate(check)`, which raises
`ValueError` with a message for the model, and `dsl_violation(trace, params, spec)`, registered
in the verifier as predicate `"dsl"`) evaluates them. Do not create `agent/checks.py`.

## API

`write_checks(llm, design_text, state, log=print, attempts=3, validate=None) -> list[dict]`

- `llm.chat(messages, max_tokens=...) -> str` is the chat client in `agent/llm.py`
  (OpenAI-style messages). Use `max_tokens=8000`: reasoning tokens count against it.
- `validate` defaults to `checks.validate`, imported inside the function so this module
  imports cleanly before `checks.py` exists; tests pass a fake.
- System prompt: the full text of `agent/checks_reference.md` (read at call time, relative to
  this file) plus instructions: write one check for every rule in the design document that
  can be observed in the game state; use object names exactly as they appear in the sample
  state; a check must be true only when the rule is broken, never during normal play; do not
  write checks for things the document does not state. Reply with exactly one JSON object
  `{"checks": [...]}` and nothing else.
- User message: the design document and the sample state as JSON (the state right after a
  level load).
- Parse the first `{` to the last `}` of the reply as JSON. Validate each check; keep the
  valid ones (first occurrence of each `id` wins). If the reply is not parseable or any check
  is invalid, and attempts remain, send a follow-up turn (keep the conversation: append the
  assistant reply and a user message listing each rejected check id with its error) asking
  for the complete corrected list, and replace the kept checks with the new valid ones only
  if the new reply has at least as many valid checks. Log one line per attempt.
- Raise `ValueError` if no valid check was obtained after all attempts.

`to_spec(checks, base=None) -> dict`

Return a verifier spec: `{"level": base.get("level"), "intentional": base.get("intentional", []),
"invariants": [{"id": c["id"], "description": c["description"], "predicate": "dsl",
"params": {"expr": c["violation"]}} for c in checks]}` (with `base` defaulting to `{}`; omit
`"level"` when `base` has none).

## Tests (`agent/test_oracle.py`, same style as `agent/test_explorer.py`: a fake LLM with
scripted replies, `t_*` functions and a `main()` runner)

Cover: valid checks on the first reply; prose around the JSON; an invalid check triggering a
retry whose feedback names the bad id and error; a worse retry not replacing a better earlier
result; unparseable replies until attempts run out raising `ValueError`; duplicate ids;
`to_spec` with and without `base`; and that the system prompt contains the reference text.
