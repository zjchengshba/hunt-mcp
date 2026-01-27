"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""
from mcp.server.fastmcp import FastMCP
# 从 MCP-tool 目录导入 dir_scan 中的注册函数（调整导入路径）
from MCP_tool.dir_scan import register_dir_scan_tool

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