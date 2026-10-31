"""Call a tool on an Unreal editor's MCP server over HTTP (stdlib only).

Lets scripts drive a second editor instance (PIE, levels, saves) with no clicks:
    python3 scripts/editor_mcp.py --port 8001 EditorToolset.EditorAppToolset StartPIE \\
        '{"options": {"bSimulate": false, "playMode": "PlayMode_InViewPort", "warmupSeconds": 0}}'
Prints the tool result. Exits 1 if the server returned an error.
"""
import argparse
import json
import sys
import urllib.request

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # localhost only


def _post(url, payload, session=None):
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, json.dumps(payload).encode(), headers, method="POST")
    with _OPENER.open(req, timeout=300) as resp:
        body = resp.read().decode("utf-8", "replace")
        session = resp.headers.get("Mcp-Session-Id") or session
    if body.lstrip().startswith("{"):
        return (json.loads(body) if body.strip() else None), session
    # Streamable HTTP may answer as server-sent events: the JSON-RPC reply is a data line.
    data = [ln[5:].strip() for ln in body.splitlines() if ln.startswith("data:")]
    return (json.loads(data[-1]) if data else None), session


def call(port, toolset, tool, arguments=None, path="/mcp"):
    url = f"http://127.0.0.1:{port}{path}"
    reply, session = _post(url, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "playtester-scripts", "version": "1"}}})
    _post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session)
    reply, _ = _post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "call_tool", "arguments": {"toolset_name": toolset, "tool_name": tool,
                                           "arguments": arguments or {}}}}, session)
    if reply is None or "error" in reply:
        raise RuntimeError(f"MCP error: {reply}")
    result = reply["result"]
    text = "".join(c.get("text", "") for c in result.get("content", []))
    if result.get("isError"):
        raise RuntimeError(text)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("toolset")
    parser.add_argument("tool")
    parser.add_argument("arguments", nargs="?", default="{}")
    args = parser.parse_args()
    try:
        print(call(args.port, args.toolset, args.tool, json.loads(args.arguments)))
    except Exception as exc:  # report and fail: callers check the exit code
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
