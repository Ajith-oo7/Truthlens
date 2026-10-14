from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def serve(name: str, register) -> None:
    server = FastMCP(name)
    register(server)
    server.run()
