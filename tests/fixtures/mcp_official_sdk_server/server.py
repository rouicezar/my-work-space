#!/usr/bin/env python3
"""Independent MCP stdio server backed by the official Python SDK."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


server = FastMCP("forma-ai-interop")


@server.tool()
def echo(message: str) -> str:
    """Echo one message for transport interoperability verification."""

    return message


if __name__ == "__main__":
    server.run(transport="stdio")
