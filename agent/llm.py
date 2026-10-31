"""OpenAI-compatible chat-completions client (standard library only)."""

import base64
import http.client
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

PROVIDERS = {
    "meta": {"base_url": "https://api.meta.ai/v1", "key_env": "META_API_KEY",
             "auth": "Bearer", "model": "muse-spark-1.3",
             "price_in": 1.25, "price_out": 4.25},
    "baseten": {"base_url": "https://inference.baseten.co/v1",
                "key_env": "BASETEN_API_KEY",
                "auth": "Api-Key", "model": "meta-models/muse-spark-open-1026",
                "price_in": 0.0, "price_out": 0.0},
}  # prices are USD per million tokens

MAX_ATTEMPTS = 3
BACKOFF_S = (2, 4)
TIMEOUT_S = 120


def load_env(path) -> dict:
    """Parse KEY=VALUE lines; ignore blanks and #comments, strip optional quotes."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    values = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key[:7].lower() == "export ":
            key = key[7:].strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def image_part(path) -> dict:
    """Build a chat message part embedding a PNG image as a data URL."""
    raw = Path(path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return {"type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encoded}"}}


class ChatClient:
    def __init__(self, base_url, api_key, model, auth="Bearer",
                 price_in=0.0, price_out=0.0):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.auth = auth
        self.price_in = price_in
        self.price_out = price_out
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0

    @property
    def cost_usd(self) -> float:
        return (self.prompt_tokens * self.price_in
                + self.completion_tokens * self.price_out) / 1_000_000

    def chat(self, messages, max_tokens=4000) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"
        body = json.dumps({"model": self.model, "messages": messages,
                           "max_tokens": max_tokens}).encode("utf-8")
        headers = {"Content-Type": "application/json",
                   "Authorization": f"{self.auth} {self.api_key}"}
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        last_status = None
        last_body = ""
        for attempt in range(MAX_ATTEMPTS):
            request = urllib.request.Request(url, data=body, headers=headers,
                                             method="POST")
            try:
                with opener.open(request, timeout=TIMEOUT_S) as response:
                    data = json.loads(response.read().decode("utf-8") or "{}")
            except urllib.error.HTTPError as exc:
                try:
                    err_body = exc.read().decode("utf-8", "replace")
                except Exception:
                    err_body = ""
                status = exc.code
                if status == 429 or (isinstance(status, int)
                                     and 500 <= status <= 599):
                    last_status, last_body = status, err_body
                else:
                    raise RuntimeError(
                        f"chat request failed with status {status}: "
                        f"{err_body}") from None
            except (urllib.error.URLError, OSError,
                    http.client.HTTPException) as exc:
                last_status, last_body = None, str(exc)
            else:
                return self._record(data)
            if attempt < MAX_ATTEMPTS - 1:
                delay = (BACKOFF_S[attempt] if attempt < len(BACKOFF_S)
                         else BACKOFF_S[-1])
                time.sleep(delay)
        if last_status is None:
            raise RuntimeError(
                f"chat request failed after {MAX_ATTEMPTS} attempts: "
                f"{last_body}")
        raise RuntimeError(
            f"chat request failed with status {last_status}: {last_body}")

    def _record(self, data) -> str:
        try:
            choices = data.get("choices", [])
            message = choices[0].get("message", {}) if choices else {}
            content = message.get("content", "")
        except (AttributeError, IndexError, TypeError):
            content = ""
        if content is None:
            content = ""
        usage = {}
        try:
            usage = data.get("usage", {}) or {}
        except AttributeError:
            usage = {}
        try:
            self.prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
            self.completion_tokens += int(usage.get("completion_tokens", 0)
                                          or 0)
        except (TypeError, ValueError):
            pass
        self.calls += 1
        return content


def from_env(provider="meta", env_path=None, model=None) -> ChatClient:
    try:
        config = PROVIDERS[provider]
    except KeyError:
        raise RuntimeError(f"unknown provider: {provider}") from None
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    file_values = load_env(env_path)
    key_env = config["key_env"]
    api_key = os.environ.get(key_env) or file_values.get(key_env)
    if not api_key:
        raise RuntimeError(
            f"missing API key: set {key_env} in the environment "
            f"or in {env_path}")
    return ChatClient(base_url=config["base_url"], api_key=api_key,
                      model=model or config["model"], auth=config["auth"],
                      price_in=config["price_in"],
                      price_out=config["price_out"])
