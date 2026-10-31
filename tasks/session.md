# Task: chat client (`agent/llm.py`) and one-command session runner (`agent/session.py`)

Create `agent/llm.py`, `agent/session.py`, `agent/test_llm.py`, `agent/test_session.py`.
Python 3.14, standard library only. Do not modify any other file (`agent/explorer.py` is being
written in parallel by someone else; code against the contract below and fake it in tests).
Run both test files and make sure they pass before finishing.

## `agent/llm.py`

OpenAI-compatible chat-completions client.

```python
PROVIDERS = {
    "meta":    {"base_url": "https://api.meta.ai/v1", "key_env": "META_API_KEY",
                "auth": "Bearer", "model": "muse-spark-1.3", "price_in": 1.25, "price_out": 4.25},
    "baseten": {"base_url": "https://inference.baseten.co/v1", "key_env": "BASETEN_API_KEY",
                "auth": "Api-Key", "model": "meta-models/muse-spark-open-1026",
                "price_in": 0.0, "price_out": 0.0},
}   # prices are USD per million tokens

def load_env(path) -> dict          # parse KEY=VALUE lines (ignore blanks and #comments,
                                    # strip optional quotes); never print values
def image_part(path) -> dict        # {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}

class ChatClient:
    def __init__(self, base_url, api_key, model, auth="Bearer", price_in=0.0, price_out=0.0)
    def chat(self, messages, max_tokens=4000) -> str
        # POST {base_url}/chat/completions with {"model", "messages", "max_tokens"}.
        # Header "Authorization: {auth} {api_key}". Timeout 120 s. Bypass any HTTP proxy
        # (urllib ProxyHandler({})). Retry up to 3 times with 2 s, 4 s backoff on HTTP 429,
        # 5xx and connection errors; raise RuntimeError with status and body otherwise.
        # Return choices[0].message.content ("" if None: reasoning models can spend the whole
        # budget on reasoning). Accumulate usage into the attributes below.
    prompt_tokens: int
    completion_tokens: int
    calls: int
    @property cost_usd -> float     # from accumulated tokens and prices

def from_env(provider="meta", env_path=None, model=None) -> ChatClient
    # env_path default: repo root .env (two levels up from this file). Environment
    # variables override the file. Raise RuntimeError naming the missing variable.
```

Never log or include the API key in exceptions.

## Explorer contract (implemented elsewhere, in `agent/explorer.py`)

```python
def explore(ue, llm, spec, shots_dir, max_turns=40, deadline_s=360.0, log=print) -> dict
# returns {"hypotheses": [h, ...], "actions": int}
# h = {"title": str, "hypothesis": str, "invariant": str, "steps": [step dicts],
#      "before": Path | None, "after": Path | None}     # screenshots inside shots_dir
```

## `agent/session.py`

```
python3 agent/session.py [--provider meta|baseten] [--model ID] [--turns N] [--minutes M]
```

1. Create `runs/<YYYYmmdd-HHMMSS>/` at the repo root with a `shots/` subfolder.
2. Build the client with `llm.from_env(provider, model=...)`, load `agent/spec.json` with
   `verifier.load_spec`.
3. Call `explorer.explore(ue, client, spec, shots_dir, max_turns=N, deadline_s=...)`.
   Default N=40; default total budget M=10 minutes, of which exploration gets 60%.
4. Verify each hypothesis with `verifier.verify(ue, h["steps"], h["invariant"], spec)`, in
   order, but skip (do not re-verify) a hypothesis whose invariant was already confirmed in
   this session; record it as rejected with reason "duplicate of a confirmed bug". A
   hypothesis whose verification raises `ValueError` is rejected with that message as reason.
5. Build findings for `report.write_report(run_dir, session, findings)`: title, hypothesis,
   invariant, invariant_description (from spec), steps, verdict, and before/after as paths
   relative to run_dir (or None). session = {started (ISO), model, actions, cost_usd (rounded
   to 4 decimals), duration_s}.
6. Also write `run_dir/session.json` with session, findings and the raw hypotheses
   (Paths as strings).
7. Print the report path and a one-line summary. Exit code 0.

Keep `main(argv=None, ue=None, client=None, explorer_mod=None, now=None)` injectable so tests
can pass fakes; real modules are imported only when not injected. Import `ue`, `verifier`,
`report` as sibling modules (the scripts run as `python3 agent/session.py`).

## Tests

- `test_llm.py` with a fake HTTP server (http.server on a free port): request body and
  auth header; usage and cost accumulate; retry on 500 then success; 400 raises without
  retry and the message does not contain the key; `content: null` returns "";
  `load_env` parsing; `from_env` with a temp env file and missing-variable error.
- `test_session.py` with fake ue, client and explorer: run_dir layout, duplicate skipping,
  ValueError rejection, report and session.json written, relative screenshot paths.
