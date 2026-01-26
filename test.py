"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""
from mcp.server.fastmcp import FastMCP
# 导入必要模块：subprocess用于调用外部脚本，os用于路径校验
import subprocess
import os

# Create an MCP server
mcp = FastMCP("Demo", json_response=True)

# 配置dirsearch.py的绝对路径（直接使用你提供的路径）
DIRSEARCH_PATH = r"D:\gongju\Rabbit_Treasure_Box_v1.0\toosl\Information_collection\directory_scan\dirsearch-0.4.3\dirsearch-0.4.3\dirsearch.py"


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def say_hello(a: str) -> str:
    """Add one sentence"""
    return "Hello " + a


# 新增：目录扫描工具（调用dirsearch.py）
@mcp.tool()
def dir_scan(target_url: str, threads: int = 10, timeout: int = 300) -> str:
    """
    调用dirsearch对目标URL进行目录扫描
    :param target_url: 待扫描的目标URL（必填，如https://www.example.com）
    :param threads: 扫描线程数，默认10（可选）
    :param timeout: 扫描超时时间（秒），默认30（可选）
    :return: 扫描结果（成功返回输出，失败返回错误信息）
    """
    # 步骤1：校验dirsearch.py文件是否存在
    if not os.path.exists(DIRSEARCH_PATH):
        return f"错误：dirsearch.py文件不存在，请检查路径是否正确：\n{DIRSEARCH_PATH}"

    # 步骤2：校验目标URL是否合法（简单校验，确保包含http/https）
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        return "错误：目标URL格式不合法，请以http://或https://开头（如https://www.example.com）"

    # 步骤3：构建dirsearch执行命令（使用python调用py脚本，传入核心参数）
    # 核心参数说明：
    # -u：指定目标URL
    # -t：指定线程数
    # -T：指定超时时间
    # --quiet：精简输出（可选，如需详细输出可删除该参数）
    cmd = [
        # 只保留一个正确的Python解释器绝对路径（去掉多余的 "python"）
        r'C:\Users\Lenovo\AppData\Local\Programs\Python\Python38\python.exe',
        DIRSEARCH_PATH,  # 补充上 dirsearch.py 的路径（关键遗漏项）
        "-u", target_url,
        "-i", '200'
    ]

    try:
        # 步骤4：执行命令并捕获输出（stdout=subprocess.PIPE：捕获标准输出；stderr=subprocess.STDOUT：将错误输出合并到标准输出）
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",  # 编码格式，避免中文乱码
            timeout=timeout + 60,  # 整体执行超时（比扫描超时多60秒，预留脚本启动时间）
            shell=False  # Windows环境下若出现问题，可改为True（不推荐，存在安全风险）
        )

        # 步骤5：处理执行结果
        if result.returncode == 0:
            # 返回码0表示执行成功，返回扫描结果
            return f"目录扫描完成（目标：{target_url}）\n-------------------------\n{result.stdout}"
        else:
            # 返回码非0表示执行失败，返回错误信息
            return f"目录扫描执行失败（目标：{target_url}）\n-------------------------\n错误信息：\n{result.stdout}"

    except subprocess.TimeoutExpired:
        return f"错误：扫描超时（已超过{timeout + 60}秒），请增大超时时间后重试"
    except Exception as e:
        return f"错误：扫描过程中出现未知异常：\n{str(e)}"


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