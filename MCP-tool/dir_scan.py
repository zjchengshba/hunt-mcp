# dir_scan_tool.py
# 单独存放目录扫描工具，解耦核心业务代码
import subprocess
import os
# 从配置文件导入路径信息
from config import PYTHON_EXECUTABLE_PATH, DIRSEARCH_PATH

def register_dir_scan_tool(mcp):
    """
    注册目录扫描工具到FastMCP实例
    :param mcp: FastMCP实例对象
    :return: 无
    """
    @mcp.tool()
    def dir_scan(target_url: str, threads: int = 10, timeout: int = 300) -> str:
        """
        调用dirsearch对目标URL进行目录扫描
        :param target_url: 待扫描的目标URL（必填，如https://www.example.com）
        :param threads: 扫描线程数，默认10（可选）
        :param timeout: 扫描超时时间（秒），默认300（可选，注意你原注释写的30，代码里是300，已统一）
        :return: 扫描结果（成功返回输出，失败返回错误信息）
        """
        # 步骤1：校验dirsearch.py文件是否存在
        if not os.path.exists(DIRSEARCH_PATH):
            return f"错误：dirsearch.py文件不存在，请检查路径是否正确：\n{DIRSEARCH_PATH}"

        # 步骤2：校验目标URL是否合法（简单校验，确保包含http/https）
        if not (target_url.startswith("http://") or target_url.startswith("https://")):
            return "错误：目标URL格式不合法，请以http://或https://开头（如https://www.example.com）"

        # 步骤3：构建dirsearch执行命令
        cmd = [
            PYTHON_EXECUTABLE_PATH,  # 从配置文件导入Python解释器路径
            DIRSEARCH_PATH,           # 从配置文件导入dirsearch路径
            "-u", target_url,
            "-t", str(threads),       # 补充你原代码遗漏的线程数参数（原代码只定义了threads，没传入cmd）
            "-T", str(timeout),       # 补充你原代码遗漏的超时时间参数（原代码只定义了timeout，没传入cmd）
            "-i", '200'
        ]

        try:
            # 步骤4：执行命令并捕获输出
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                timeout=timeout + 60,  # 整体执行超时（预留脚本启动时间）
                shell=False
            )

            # 步骤5：处理执行结果
            if result.returncode == 0:
                return f"目录扫描完成（目标：{target_url}）\n-------------------------\n{result.stdout}"
            else:
                return f"目录扫描执行失败（目标：{target_url}）\n-------------------------\n错误信息：\n{result.stdout}"

        except subprocess.TimeoutExpired:
            return f"错误：扫描超时（已超过{timeout + 60}秒），请增大超时时间后重试"
        except Exception as e:
            return f"错误：扫描过程中出现未知异常：\n{str(e)}"