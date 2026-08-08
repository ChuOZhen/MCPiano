"""Manual sanity check for the MCPiano MCP server.

Starts ``mcp_server.py`` as a subprocess, sends a ``tools/list`` request,
and prints the response.  Useful for verifying stdio JSON-RPC works before
loading the server into KimiCode.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

TOOLCHAIN_DIR = Path(__file__).resolve().parents[1] / "toolchain"


def main():
    """Run a quick JSON-RPC exchange with the MCP server."""
    env = {"PYTHONPATH": str(TOOLCHAIN_DIR)}
    proc = subprocess.Popen(
        [sys.executable, str(TOOLCHAIN_DIR / "mcp_server.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, **env},
    )

    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test_client", "version": "0.1"},
        },
    }
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }

    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.write(json.dumps(tools_request) + "\n")
    proc.stdin.flush()

    for _ in range(2):
        line = proc.stdout.readline()
        if line:
            print(line.strip())

    proc.terminate()
    proc.wait(timeout=2)


if __name__ == "__main__":
    main()
