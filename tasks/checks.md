# Task: interpreter for model-written checks (`agent/checks.py`)

Create `agent/checks.py` and `agent/test_checks.py`, and register the new predicate in
`agent/verifier.py` (one import and one `PREDICATES` entry; change nothing else there).
Python 3.14, standard library only. Do not modify any other file. Run every
`agent/test_*.py` and make sure all pass before finishing.

## Why

An LLM reads a game's design document and writes checks in a small JSON language. A
deterministic verifier must evaluate them, so the LLM never decides whether a bug is real.
The language is specified in `agent/checks_reference.md`: **read it first; it is the
contract**. Model output is untrusted: never use `eval`, `exec` or anything that runs code.

## API

- `validate(check) -> None`: raise `ValueError` with a short, specific message (it is fed
  back to the model) unless `check` is a dict with exactly the keys `id`, `description` and
  `violation`; `id` matches `^[a-z][a-z0-9_]{0,63}$`; `description` is a non-empty string
  of at most 500 chars; and `violation` is a valid expression. A valid expression is a
  literal (number, string up to 200 chars, bool, null) or a dict with exactly one key that
  is a known operator with the right argument shape: `var`/`prev`/`first` take a path
  string matching `^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$`; `did` takes one of `move_to`,
  `look_at`, `jump`, `interact`, `step`; `dist` takes a list of two paths; comparisons,
  `+` and `-` take a list of two expressions; `and`/`or` take a non-empty list of
  expressions; `not`, `ever`, `always` and `final` take one expression; `after` takes a list
  of two expressions. Reject expressions deeper than 12 levels or with more than 200 nodes.
- `evaluate(trace, expr) -> bool`: evaluate a validated expression over a trace
  `[{"action": None | {"action": "<type>", ...}, "state": {...}}, ...]` exactly as the
  reference describes. The top level is evaluated at the last index. The result counts as a
  violation only if it is truthy (`null` is false). Never raise on odd state contents
  (missing keys, wrong types): they give `null` / false.
- `dsl_violation(trace, params, spec) -> bool`: `evaluate(trace, params["expr"])`; this is
  the verifier predicate.

In `agent/verifier.py`, register it as `PREDICATES["dsl"]`.

## Tests (`agent/test_checks.py`, same style as `agent/test_verifier.py`: plain asserts,
`t_*` functions and a `main()` runner)

Cover: each operator on small hand-made traces; `prev`/`first` at the first state; `after`
needing the last state to be strictly later; `did`; `dist`; `null` handling; both examples
from `checks_reference.md` (true and false cases); `validate` rejecting unknown operators,
bad paths, two-key dicts, too-deep and too-large expressions and bad ids; and
`verifier.verify` confirming a `dsl` invariant with a fake `ue` (see `agent/test_verifier.py`).
