from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import time
import os
import json
import re
from datetime import datetime
from config import BURP_LOG_PATH, SELENIUM_PATH

# ===================== 全局配置（只改这里！）=====================
# 本地Burp日志路径（确保日志文件在当前目录，或写绝对路径）
BURP_LOG_PATH = BURP_LOG_PATH  # 直接指定路径，无需依赖外部config.py
# 目标URL关键词（无需修改，匹配dipp.sf-express.com）
TARGET_URL_KEYWORD = "dipp.sf-express.com"
# 目标页面URL（无需修改）
TARGET_URL = "https://dipp.sf-express.com/"
# Burp代理（默认本地8080，无需修改）
BURP_PROXY = "127.0.0.1:8080"
# 导出目录（默认当前目录）
EXPORT_DIR = "./"

def register_selenium_tool(mcp):
    """
    注册Selenium自动化工具到FastMCP实例
    :param mcp: FastMCP实例对象
    :return: 无
    """
    @mcp.tool()
    def selenium_automation(target_url: str = TARGET_URL, wait_time: int = 15) -> str:
        """
        使用Selenium自动化访问目标URL并筛选Burp日志中的JSON响应
        :param target_url: 目标URL（默认：https://dipp.sf-express.com/）
        :param wait_time: 手动操作等待时间（默认：15秒）
        :return: 操作结果和筛选到的JSON响应数量
        """
        # 步骤1：启动浏览器+Burp代理
        driver = selenium_burp_automation_edge(target_url, BURP_PROXY)

        if not driver:
            return "错误：浏览器启动失败"

        # 步骤2：预留手动操作时间
        time.sleep(wait_time)

        # 步骤3：执行日志筛选
        try:
            # 检查日志文件是否存在
            if not os.path.exists(BURP_LOG_PATH):
                driver.quit()
                return f"错误：Burp日志文件不存在：{BURP_LOG_PATH}"

            # 读取日志内容
            with open(BURP_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                raw_log_content = f.read()

            if not raw_log_content.strip():
                driver.quit()
                return "错误：Burp日志文件为空"

            # 执行筛选
            filtered_log_content, valid_count = filter_burp_log_for_json(raw_log_content)

            # 生成带时间戳的导出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = TARGET_URL_KEYWORD.replace('/', '_').replace(':', '')
            export_filename = f"{EXPORT_DIR}burp_json_valid_{safe_keyword}_{timestamp}.log"

            # 写入筛选结果
            with open(export_filename, "w", encoding="utf-8") as f:
                f.write(filtered_log_content)

            # 关闭浏览器
            driver.quit()

            return f"操作完成！\n导出文件：{os.path.abspath(export_filename)}\n筛选到 {valid_count} 条JSON响应"
        except Exception as e:
            driver.quit()
            return f"错误：{str(e)}"

    @mcp.tool()
    def filter_burp_log(log_file: str = BURP_LOG_PATH) -> str:
        """
        筛选Burp日志中的JSON响应
        :param log_file: Burp日志文件路径（默认：从配置文件读取）
        :return: 筛选结果和导出文件路径
        """
        try:
            # 检查日志文件是否存在
            if not os.path.exists(log_file):
                return f"错误：Burp日志文件不存在：{log_file}"

            # 读取日志内容
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                raw_log_content = f.read()

            if not raw_log_content.strip():
                return "错误：Burp日志文件为空"

            # 执行筛选
            filtered_log_content, valid_count = filter_burp_log_for_json(raw_log_content)

            # 生成带时间戳的导出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = TARGET_URL_KEYWORD.replace('/', '_').replace(':', '')
            export_filename = f"{EXPORT_DIR}burp_json_valid_{safe_keyword}_{timestamp}.log"

            # 写入筛选结果
            with open(export_filename, "w", encoding="utf-8") as f:
                f.write(filtered_log_content)

            return f"筛选完成！\n导出文件：{os.path.abspath(export_filename)}\n筛选到 {valid_count} 条JSON响应"
        except Exception as e:
            return f"错误：{str(e)}"


# ===================== Selenium部分（自动打开浏览器+Burp代理）=====================
def selenium_burp_automation_edge(target_url, burp_proxy="127.0.0.1:8080"):
    edge_options = Options()
    edge_options.add_argument(f'--proxy-server=http://{burp_proxy}')
    edge_options.add_argument('--ignore-certificate-errors')
    edge_options.add_argument('--ignore-ssl-errors')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument('--disable-popup-blocking')

    try:
        driver_path = SELENIUM_PATH
        driver_service = Service(executable_path=driver_path) if os.path.exists(driver_path) else Service()
    except Exception:
        driver_service = Service()

    driver = webdriver.Edge(service=driver_service, options=edge_options)
    driver.maximize_window()

    try:
        print(f"\n✅ 正在访问目标页面：{target_url}")
        driver.get(target_url)
        # 等待页面加载（放宽条件，无需等待title，只要页面不报错即可）
        WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"✅ 页面加载完成，可手动操作浏览器（如登录、触发接口），15秒后自动筛选日志")
    except Exception as e:
        print(f"❌ 自动化操作失败：{str(e)}")
        driver.quit()
        return None
    return driver


# ===================== 核心日志筛选（按需求优化）=====================
def filter_burp_log_for_json(raw_log_content):
    # 匹配日志的等号分隔符（使用正确的格式）
    traffic_separator = "======================================================"
    # 拆分流量条目，过滤空内容
    traffic_entries = [entry.strip() for entry in raw_log_content.split(traffic_separator) if entry.strip()]
    valid_entries = []

    # 匹配响应头中的Content-Type: application/json（严格匹配）
    content_type_json_pattern = re.compile(r'Content-Type:\s*application/json', re.IGNORECASE)

    print(f"\n🔍 日志解析开始：共检测到 {len(traffic_entries)} 条日志条目")
    print(f"📋 筛选规则：URL含[{TARGET_URL_KEYWORD}] + 响应头含[application/json]")

    # 统计变量
    url_match_count = 0
    json_response_count = 0
    final_valid_count = 0

    current_request = None
    for idx, entry in enumerate(traffic_entries, 1):
        # 检查是否是目标URL的请求
        if TARGET_URL_KEYWORD.lower() in entry.lower() and ('GET' in entry or 'POST' in entry):
            current_request = entry
            url_match_count += 1

        # 检查是否是返回包且Content-Type为application/json
        elif current_request and 'HTTP/' in entry:
            # 严格检查Content-Type是否为application/json
            if content_type_json_pattern.search(entry):
                # 提取完整的返回包
                response = entry
                # 添加到结果中
                valid_entries.append(current_request)
                valid_entries.append(response)
                json_response_count += 1
                final_valid_count += 1
                # 重置当前请求
                current_request = None
            else:
                # 如果返回包不是JSON格式，重置当前请求
                current_request = None

    # 打印筛选统计
    print(
        f"📊 筛选结果：URL匹配[{url_match_count}]条 → JSON响应头匹配[{json_response_count}]条 → 最终有效[{final_valid_count}]条")
    if final_valid_count == 0:
        print("⚠️  无有效条目：可能未触发JSON接口，或日志中无相关流量")

    # 用正确的分隔符重组日志
    filtered_log = traffic_separator + "\n\n" + ("\n\n" + traffic_separator + "\n\n").join(valid_entries) + "\n\n" + traffic_separator
    return filtered_log, final_valid_count


# ===================== 日志导出+主流程=====================
def run_json_log_filter():
    try:
        # 检查日志文件是否存在
        if not os.path.exists(BURP_LOG_PATH):
            print(f"❌ 未找到Burp日志文件：{BURP_LOG_PATH}")
            return
        # 读取日志内容（忽略编码错误，完整保留原始字符）
        with open(BURP_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            raw_log_content = f.read()
        if not raw_log_content.strip():
            print("❌ Burp日志文件为空")
            return

        # 执行筛选
        filtered_log_content, valid_count = filter_burp_log_for_json(raw_log_content)

        # 生成带时间戳的导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = TARGET_URL_KEYWORD.replace('/', '_').replace(':', '')
        export_filename = f"{EXPORT_DIR}burp_json_valid_{safe_keyword}_{timestamp}.log"

        # 写入筛选结果
        with open(export_filename, "w", encoding="utf-8") as f:
            f.write(filtered_log_content)

        print(f"\n✅ 筛选完成！导出文件：{os.path.abspath(export_filename)}")
        print(f"📌 导出内容：{valid_count} 条完整流量（每条含请求头、请求体、响应头、JSON响应体）")
    except Exception as e:
        print(f"❌ 筛选异常：{str(e)}")


# ===================== 程序入口=====================
if __name__ == "__main__":
    print("=" * 80)
    print("  Burp日志JSON流量提取工具（Selenium自动化版）")
    print("=" * 80)

    # 步骤1：启动浏览器+Burp代理（自动走Burp抓包）
    driver = selenium_burp_automation_edge(TARGET_URL, BURP_PROXY)

    # 步骤2：预留15秒手动操作时间（可修改时长，用于触发JSON接口）
    WAIT_TIME = 15
    time.sleep(WAIT_TIME)

    # 步骤3：执行日志筛选
    print("\n" + "=" * 60)
    print("  开始筛选Burp日志...")
    print("=" * 60)
    run_json_log_filter()

    # 步骤4：保持浏览器打开，支持后续操作
    if driver:
        print(f"\nℹ️  浏览器保持打开，可继续触发接口；按Ctrl+C关闭浏览器和脚本")
        try:
            while True:
                time.sleep(3600)  # 持续运行，直到手动终止
        except KeyboardInterrupt:
            print(f"\nℹ️  手动终止，关闭浏览器...")
            driver.quit()
