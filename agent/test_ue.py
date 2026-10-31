"""Fake-server tests for ue.py. Run: python agent/test_ue.py"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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
            if self.server.b_stepping:
                self.server.polls += 1
                if self.server.mode != "stuck" and self.server.polls >= 2:
                    self.server.b_stepping = False
                    self.server.step_id += 1
            self._reply({"StepId": self.server.step_id, "bStepping": self.server.b_stepping})
        elif fn == "Step":
            self.server.b_stepping = True
            self.server.polls = 0
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
    finally:
        server.shutdown()

    print("all tests passed")


if __name__ == "__main__":
    main()
