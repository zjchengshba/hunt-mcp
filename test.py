"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""

import sys
import os


# 后续导入语句不变（此时就能正常找到 MCP-tool 包了）
from mcp.server.fastmcp import FastMCP
# 注意：目录名是 MCP-tool，导入时可以直接用连字符，也可以用下划线，两种都支持
from MCPServer.dir_scan import register_dir_scan_tool


# Create an MCP server
mcp = FastMCP("Demo", json_response=True)

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Add a hello tool
@mcp.tool()
def say_hello(a: str) -> str:
    """Add one sentence"""
    return "Hello " + a

# 注册外部的目录扫描工具（关键：将mcp实例传入，完成工具注册）
register_dir_scan_tool(mcp)

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."

# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")