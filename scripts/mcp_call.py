"""Minimal MCP stdio client for this workshop's Blender chain.

agent -> stdio JSON-RPC -> blender-mcp -> TCP localhost:9876 -> Blender MCP extension

The host agent may not expose MCP tools directly; this script performs the same
protocol the client would. Usage:

    python scripts/mcp_call.py list-tools
    python scripts/mcp_call.py summarize
    python scripts/mcp_call.py exec path/to/snippet.py
    python scripts/mcp_call.py exec -            # read snippet from stdin
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading

SERVER = os.environ.get("BLENDER_MCP_BIN", "blender-mcp")
TIMEOUT = float(os.environ.get("BLENDER_MCP_TIMEOUT", "900"))


class McpStdio:
    def __init__(self, server: str = SERVER) -> None:
        self.proc = subprocess.Popen(
            [server, "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._id = 0
        self._err_lines: list[str] = []
        self._err_thread = threading.Thread(target=self._drain_err, daemon=True)
        self._err_thread.start()

    def _drain_err(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self._err_lines.append(line.rstrip())
            if len(self._err_lines) > 400:
                del self._err_lines[:200]

    def _send(self, payload: dict) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

    def _recv(self) -> dict:
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(
                    "blender-mcp closed the stream.\nstderr:\n"
                    + "\n".join(self._err_lines[-40:])
                )
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                # non-protocol chatter on stdout
                self._err_lines.append("stdout: " + line)

    def request(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        rid = self._id
        msg = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)
        while True:
            resp = self._recv()
            if resp.get("id") != rid:
                continue  # notification or unrelated message
            if "error" in resp:
                raise RuntimeError(json.dumps(resp["error"], indent=2))
            return resp.get("result", {})

    def notify(self, method: str, params: dict | None = None) -> None:
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def initialize(self) -> dict:
        result = self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "workshop-mcp-client", "version": "1.0.0"},
            },
        )
        self.notify("notifications/initialized", {})
        return result

    def list_tools(self) -> list[dict]:
        out: list[dict] = []
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            res = self.request("tools/list", params)
            out.extend(res.get("tools", []))
            cursor = res.get("nextCursor")
            if not cursor:
                return out

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        return self.request("tools/call", {"name": name, "arguments": arguments or {}})

    def close(self) -> None:
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def _text_of(result: dict) -> str:
    parts = []
    for item in result.get("content", []):
        if item.get("type") == "text":
            parts.append(item.get("text", ""))
        else:
            parts.append(json.dumps(item))
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    client = McpStdio()
    try:
        info = client.initialize()
        if cmd == "list-tools":
            for tool in client.list_tools():
                print(f"- {tool['name']}: {tool.get('description', '')[:110]}")
            return 0
        if cmd == "call":
            name = argv[2]
            args = json.loads(argv[3]) if len(argv) > 3 else {}
            res = client.call_tool(name, args)
            print(_text_of(res))
            return 0 if not res.get("isError") else 1
        if cmd == "summarize":
            res = client.call_tool("get_objects_summary", {})
            print(_text_of(res))
            return 0 if not res.get("isError") else 1
        if cmd == "exec":
            if len(argv) < 3:
                print("exec needs a script path or -", file=sys.stderr)
                return 2
            src = argv[2]
            code = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
            res = client.call_tool("execute_blender_code", {"code": code})
            print(_text_of(res))
            return 0 if not res.get("isError") else 1
        print(f"unknown command {cmd}", file=sys.stderr)
        return 2
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
