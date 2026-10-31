# Task: `agent/ue.py`, a tiny Remote Control client for BP_TestHarness

Write two files and nothing else: `agent/ue.py` and `agent/test_ue.py`. Python 3.14,
standard library only (no new dependencies). Keep `ue.py` under ~60 lines.

## Context

Unreal Engine's Remote Control API listens on `http://127.0.0.1:30010`. A Blueprint actor
`BP_TestHarness` lives in the running game. Calling one of its functions is:

```
PUT /remote/object/call
Content-Type: application/json
{"objectPath": "<HARNESS_PATH>", "functionName": "<Name>", "parameters": {...}, "generateTransaction": false}
```

The response body is a JSON object with the function's output parameters by name
(empty object `{}` for functions without outputs). Errors come back as HTTP 4xx/5xx.

The game is turn-based. `Step(Seconds)` unpauses the game and returns immediately; the harness
re-pauses after `Seconds` of game time and increments `StepId`. `GetState()` returns at least
`{"StepId": int, "bStepping": bool, ...}`.

## API to implement in `agent/ue.py`

```python
BASE_URL = "http://127.0.0.1:30010"
HARNESS_PATH = "/Game/Maps/UEDPIE_0_Arena.Arena:PersistentLevel.BP_TestHarness"

class UEError(Exception): ...

def call(function: str, **params) -> dict
    # PUT as above; raise UEError with status and response body on HTTP error or
    # connection failure; timeout 10 s.

def state() -> dict
    # call("GetState")

def step(seconds: float, timeout: float = 30.0) -> dict
    # read StepId, call("Step", Seconds=seconds), poll state() every 0.05 s until
    # StepId increased and bStepping is false; return that state.
    # Raise UEError if timeout elapses.
```

Read `BASE_URL` and `HARNESS_PATH` from the environment variables `UE_RC_URL` and
`UE_HARNESS_PATH` when set, otherwise use the defaults above.

## Tests in `agent/test_ue.py`

Plain `assert`s runnable with `python agent/test_ue.py` (no pytest). Start a fake Remote
Control server with `http.server` on a free port in a background thread that implements
`GetState` and `Step` (Step advances StepId after a couple of polls). Cover:
1. `call` sends the exact JSON body above and returns the parsed response.
2. `step` returns the state with the incremented StepId.
3. `step` raises `UEError` on timeout when the fake server never advances.
4. HTTP 400 from the server raises `UEError`.

Run the tests and make sure they pass before finishing. Do not touch any other file.
