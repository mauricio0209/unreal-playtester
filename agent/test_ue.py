"""Fake-server tests for ue.py. Run: python agent/test_ue.py"""

import json
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ue


class Handler(BaseHTTPRequestHandler):
    def _reply(self, obj, status=200):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_PUT(self):
        if self.path != "/remote/object/call":
            self._reply({"error": "not found"}, 404)
            return
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")
        self.server.last_body = req
        fn = req.get("functionName")
        if fn == "GetState":
            if getattr(self.server, "fail_getstate", 0) > 0:
                self.server.fail_getstate -= 1
                self._reply({"error": "loading"}, 500)
                return
            if self.server.b_stepping:
                self.server.polls += 1
                if self.server.mode != "stuck" and self.server.polls >= 2:
                    self.server.b_stepping = False
                    self.server.step_id += 1
            resp = {"StepId": self.server.step_id, "bStepping": self.server.b_stepping}
            if getattr(self.server, "boot_time", None) is not None:
                resp["BootTime"] = self.server.boot_time
            self._reply(resp)
        elif fn == "Step":
            self.server.b_stepping = True
            self.server.polls = 0
            self._reply({})
        elif fn in ("MoveTo", "Jump", "LookAt", "Interact"):
            self._reply({})
        elif fn == "Screenshot":
            if getattr(self.server, "screenshot_write", True):
                delay = getattr(self.server, "screenshot_delay", 0.2)

                def _write():
                    time.sleep(delay)
                    try:
                        d = ue.SCREENSHOT_DIR
                        d.mkdir(parents=True, exist_ok=True)
                        (d / "shot-new.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 128)
                    except OSError:
                        pass

                threading.Thread(target=_write, daemon=True).start()
            self._reply({})
        elif fn == "ResetLevel":
            if getattr(self.server, "boot_time", None) is not None:
                self.server.fail_getstate = getattr(self.server, "reset_failures", 3)
                self.server.boot_time = self.server.boot_time + 1.0
            self._reply({})
        else:
            self._reply({"error": f"unknown function {fn}"}, 400)

    def log_message(self, *a):
        pass


def reset(server, mode="normal"):
    server.step_id = 0
    server.b_stepping = False
    server.polls = 0
    server.mode = mode
    server.last_body = None
    server.boot_time = None
    server.fail_getstate = 0
    server.reset_failures = 3
    server.screenshot_write = True
    server.screenshot_delay = 0.2


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    reset(server)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    ue.BASE_URL = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        # 1. call sends exact body and returns parsed response
        reset(server)
        r = ue.call("GetState")
        assert r == {"StepId": 0, "bStepping": False}, r
        assert server.last_body == {
            "objectPath": ue.HARNESS_PATH,
            "functionName": "GetState",
            "parameters": {},
            "generateTransaction": False,
        }, server.last_body
        r = ue.call("Step", Seconds=1.5)
        assert r == {}, r
        assert server.last_body["parameters"] == {"Seconds": 1.5}, server.last_body
        print("1 ok: call body + response")

        # 2. step returns state with incremented StepId
        reset(server)
        s = ue.step(0.1, timeout=5.0)
        assert s["StepId"] == 1, s
        assert s["bStepping"] is False, s
        print("2 ok: step advances StepId")

        # 3. step raises UEError on timeout when server never advances
        reset(server, mode="stuck")
        try:
            ue.step(0.1, timeout=0.2)
        except ue.UEError:
            print("3 ok: step timeout raises UEError")
        else:
            raise AssertionError("step should have timed out")

        # 4. HTTP 400 raises UEError
        reset(server)
        try:
            ue.call("Nope")
        except ue.UEError as e:
            assert "400" in str(e), e
            print("4 ok: HTTP 400 raises UEError")
        else:
            raise AssertionError("HTTP 400 should raise UEError")

        # 5. each action sends the right functionName and parameters
        reset(server)
        ue.move_to(1.5, -2.5)
        assert server.last_body["functionName"] == "MoveTo", server.last_body
        assert server.last_body["parameters"] == {"X": 1.5, "Y": -2.5}, server.last_body
        ue.jump()
        assert server.last_body["functionName"] == "Jump", server.last_body
        assert server.last_body["parameters"] == {}, server.last_body
        ue.look_at(1.0, 2.0, 3.0)
        assert server.last_body["functionName"] == "LookAt", server.last_body
        assert server.last_body["parameters"] == {"X": 1.0, "Y": 2.0, "Z": 3.0}, server.last_body
        ue.interact()
        assert server.last_body["functionName"] == "Interact", server.last_body
        assert server.last_body["parameters"] == {}, server.last_body
        print("5 ok: actions send functionName + parameters")

        # 6. screenshot returns the new file, ignoring pre-existing PNGs
        reset(server)
        with tempfile.TemporaryDirectory() as tmp:
            old_dir = ue.SCREENSHOT_DIR
            ue.SCREENSHOT_DIR = Path(tmp)
            try:
                old = Path(tmp) / "old.png"
                old.write_bytes(b"\x89PNG\r\n\x1a\nold")
                server.screenshot_write = True
                server.screenshot_delay = 0.2
                p = ue.screenshot(timeout=5.0)
                assert p.is_file(), p
                assert p.name != old.name, p
                assert p.stat().st_size > 0, p
                assert p.parent == Path(tmp), p
                print("6 ok: screenshot returns new file")
            finally:
                ue.SCREENSHOT_DIR = old_dir

        # 7. screenshot raises UEError when no file appears
        reset(server)
        with tempfile.TemporaryDirectory() as tmp:
            old_dir = ue.SCREENSHOT_DIR
            missing = Path(tmp) / "missing"
            ue.SCREENSHOT_DIR = missing
            try:
                server.screenshot_write = False
                try:
                    ue.screenshot(timeout=0.3)
                except ue.UEError:
                    assert missing.is_dir(), missing
                    print("7 ok: screenshot timeout raises UEError")
                else:
                    raise AssertionError("screenshot should have timed out")
            finally:
                ue.SCREENSHOT_DIR = old_dir

        # 8. reset polls through HTTP 500s until BootTime changes
        reset(server)
        server.boot_time = 10.0
        server.reset_failures = 3
        server.fail_getstate = 0
        s = ue.reset(timeout=5.0)
        assert s["BootTime"] != 10.0, s
        assert s["BootTime"] == 11.0, s
        print("8 ok: reset returns new state after reload")
    finally:
        server.shutdown()

    print("all tests passed")


if __name__ == "__main__":
    main()
