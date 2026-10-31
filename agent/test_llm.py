"""Tests for llm.py. Run: python3 agent/test_llm.py"""

import http.server
import json
import os
import tempfile
import threading
from pathlib import Path

import llm

API_KEY = "test-key-xyz"


def ok_payload(content="hello", prompt=10, completion=5):
    return {"choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": prompt,
                      "completion_tokens": completion}}


class _Handler(http.server.BaseHTTPRequestHandler):
    responses = []
    requests = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            body = None
        _Handler.requests.append({
            "path": self.path,
            "auth": self.headers.get("Authorization"),
            "content_type": self.headers.get("Content-Type"),
            "body": body,
        })
        if _Handler.responses:
            status, payload = _Handler.responses.pop(0)
        else:
            status, payload = (200, ok_payload())
        if isinstance(payload, dict):
            data = json.dumps(payload).encode()
        else:
            data = payload if isinstance(payload, bytes) else str(
                payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class FakeServer:
    def __init__(self):
        _Handler.requests = []
        _Handler.responses = []
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.thread.start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


def make_client(server, **overrides):
    kwargs = {"base_url": server.url, "api_key": API_KEY,
              "model": "test-model", "price_in": 1.25, "price_out": 4.25}
    kwargs.update(overrides)
    return llm.ChatClient(**kwargs)


def patch_sleep():
    real_sleep = llm.time.sleep
    sleeps = []
    llm.time.sleep = lambda s: sleeps.append(s)
    return real_sleep, sleeps


def t_request_body_and_auth():
    server = FakeServer()
    try:
        messages = [{"role": "user", "content": "hi"}]
        client = make_client(server)
        text = client.chat(messages, max_tokens=123)
        assert text == "hello", text
        assert len(_Handler.requests) == 1
        req = _Handler.requests[0]
        assert req["path"] == "/chat/completions", req
        assert req["auth"] == f"Bearer {API_KEY}", req
        assert req["content_type"] == "application/json", req
        assert req["body"] == {"model": "test-model", "messages": messages,
                               "max_tokens": 123}, req["body"]
        text = client.chat(messages)
        assert _Handler.requests[1]["body"]["max_tokens"] == 4000
    finally:
        server.close()


def t_auth_scheme_from_client():
    server = FakeServer()
    try:
        client = make_client(server, auth="Api-Key")
        client.chat([{"role": "user", "content": "hi"}])
        assert _Handler.requests[0]["auth"] == f"Api-Key {API_KEY}"
    finally:
        server.close()


def t_usage_and_cost_accumulate():
    server = FakeServer()
    try:
        _Handler.responses = [(200, ok_payload("one", 10, 5)),
                              (200, ok_payload("two", 20, 7))]
        client = make_client(server)
        assert client.chat([{"role": "user", "content": "a"}]) == "one"
        assert client.chat([{"role": "user", "content": "b"}]) == "two"
        assert client.prompt_tokens == 30, client.prompt_tokens
        assert client.completion_tokens == 12, client.completion_tokens
        assert client.calls == 2, client.calls
        expected = (30 * 1.25 + 12 * 4.25) / 1_000_000
        assert abs(client.cost_usd - expected) < 1e-12, client.cost_usd
    finally:
        server.close()


def t_retry_500_then_success():
    server = FakeServer()
    real_sleep, sleeps = patch_sleep()
    try:
        _Handler.responses = [(500, {"error": "boom"}),
                              (200, ok_payload("recovered", 3, 4))]
        client = make_client(server)
        assert client.chat([{"role": "user", "content": "hi"}]) == "recovered"
        assert len(_Handler.requests) == 2, _Handler.requests
        assert sleeps == [2], sleeps
        assert (client.prompt_tokens, client.completion_tokens,
                client.calls) == (3, 4, 1)
    finally:
        llm.time.sleep = real_sleep
        server.close()


def t_retry_429_then_success():
    server = FakeServer()
    real_sleep, sleeps = patch_sleep()
    try:
        _Handler.responses = [(429, {"error": "slow down"}),
                              (200, ok_payload("calm", 1, 1))]
        client = make_client(server)
        assert client.chat([{"role": "user", "content": "hi"}]) == "calm"
        assert len(_Handler.requests) == 2
        assert sleeps == [2], sleeps
    finally:
        llm.time.sleep = real_sleep
        server.close()


def t_400_raises_without_retry():
    server = FakeServer()
    real_sleep, sleeps = patch_sleep()
    try:
        _Handler.responses = [(400, {"error": "bad request"})]
        client = make_client(server)
        try:
            client.chat([{"role": "user", "content": "hi"}])
        except RuntimeError as exc:
            message = str(exc)
        else:
            raise AssertionError("expected RuntimeError")
        assert len(_Handler.requests) == 1, _Handler.requests
        assert sleeps == [], sleeps
        assert "400" in message, message
        assert API_KEY not in message, message
        assert client.calls == 0
    finally:
        llm.time.sleep = real_sleep
        server.close()


def t_null_content_returns_empty():
    server = FakeServer()
    try:
        _Handler.responses = [(200, {"choices": [{"message": {
            "content": None}}], "usage": {}})]
        client = make_client(server)
        assert client.chat([{"role": "user", "content": "hi"}]) == ""
        assert client.calls == 1
        assert client.prompt_tokens == 0
        assert client.completion_tokens == 0
    finally:
        server.close()


def t_image_part():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "shot.png"
        path.write_bytes(b"\x89PNG-fake-bytes")
        part = llm.image_part(path)
        assert part["type"] == "image_url", part
        url = part["image_url"]["url"]
        assert url.startswith("data:image/png;base64,"), url
        import base64
        assert base64.b64decode(url.split(",", 1)[1]) == b"\x89PNG-fake-bytes"


def t_load_env_parsing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".env"
        path.write_text("# a comment\n"
                        "\n"
                        "FOO=bar\n"
                        "QUOTED=\"hello world\"\n"
                        "SINGLE='it works'\n"
                        "EMPTY=\n"
                        "SPACED = spaced value \n"
                        "   # indented comment\n"
                        "NOEQUALS\n",
                        encoding="utf-8")
        values = llm.load_env(path)
        assert values == {"FOO": "bar", "QUOTED": "hello world",
                          "SINGLE": "it works", "EMPTY": "",
                          "SPACED": "spaced value"}, values


def _stash_env(*names):
    saved = {}
    for name in names:
        saved[name] = os.environ.pop(name, None)
    return saved


def _restore_env(saved):
    for name, value in saved.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def t_from_env_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".env"
        path.write_text("META_API_KEY=file-key-123\n"
                        "BASETEN_API_KEY=baseten-key-456\n",
                        encoding="utf-8")
        saved = _stash_env("META_API_KEY", "BASETEN_API_KEY")
        try:
            client = llm.from_env("meta", env_path=path)
            assert client.api_key == "file-key-123", client.api_key
            assert client.base_url == "https://api.meta.ai/v1"
            assert client.model == "muse-spark-1.3", client.model
            assert client.auth == "Bearer"
            assert (client.price_in, client.price_out) == (1.25, 4.25)
            custom = llm.from_env("meta", env_path=path, model="custom-id")
            assert custom.model == "custom-id", custom.model
            base = llm.from_env("baseten", env_path=path)
            assert base.auth == "Api-Key", base.auth
            assert base.base_url == "https://inference.baseten.co/v1"
            assert base.api_key == "baseten-key-456"
        finally:
            _restore_env(saved)


def t_from_env_env_overrides_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".env"
        path.write_text("META_API_KEY=file-key\n", encoding="utf-8")
        saved = _stash_env("META_API_KEY")
        os.environ["META_API_KEY"] = "env-key-789"
        try:
            client = llm.from_env("meta", env_path=path)
            assert client.api_key == "env-key-789", client.api_key
        finally:
            _restore_env(saved)


def t_from_env_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".env"
        path.write_text("# empty\n", encoding="utf-8")
        saved = _stash_env("META_API_KEY", "BASETEN_API_KEY")
        try:
            try:
                llm.from_env("meta", env_path=path)
            except RuntimeError as exc:
                assert "META_API_KEY" in str(exc), str(exc)
            else:
                raise AssertionError("expected RuntimeError")
        finally:
            _restore_env(saved)


def main():
    tests = sorted((name, fn) for name, fn in globals().items()
                   if name.startswith("t_") and callable(fn))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
