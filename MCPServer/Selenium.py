from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import re
from datetime import datetime
from config import BURP_LOG_PATH

# ===================== 全局配置项（统一修改这里，无需改动其他代码）=====================
# 1. Selenium 配置
TARGET_URL = "https://dipp.sf-express.com/"
BURP_PROXY = "127.0.0.1:8080"

# 2. Burp 日志筛选配置（核心，根据你的需求修改）
RAW_BURP_LOG_PATH = BURP_LOG_PATH  # 你的 Burp 原始日志文件路径（需与 Burp 保存路径一致）
EXPORT_DIR = "./"  # 筛选后日志的导出目录（默认当前文件夹）
MIN_JSON_LENGTH = 5  # 最小 JSON 片段长度，过滤无意义短片段
PRESERVE_TRAFFIC_CONTEXT = True  # 保留请求头+响应头+JSON 返回体（建议设为 True）
WHITELIST_CONTENT_TYPE = "Content-Type: application/json"  # 仅保留 JSON 类型流量
TARGET_URL_KEYWORD = "dipp.sf-express.com"  # 仅保留包含该 URL/路径片段的流量


# ===================== 第一部分：Selenium 配置 Burp 代理，自动化访问页面 =====================
def selenium_burp_automation_edge(target_url, burp_proxy="127.0.0.1:8080"):
    """
    适配Edge浏览器：Selenium配置Burp代理，自动化访问页面（不关闭浏览器），让Burp捕获页面加载流量
    :param target_url: 目标页面 URL
    :param burp_proxy: Burp 代理地址（格式：ip:port）
    :return: 启动后的 driver 实例（用于后续流程判断）
    """
    # 1. 配置Edge浏览器选项
    edge_options = Options()
    edge_options.add_argument(f'--proxy-server=http://{burp_proxy}')
    edge_options.add_argument('--ignore-certificate-errors')
    edge_options.add_argument('--ignore-ssl-errors')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument('--disable-popup-blocking')

    # 2. 配置EdgeDriver路径
    try:
        driver_path = "./msedgedriver.exe"
        if not os.path.exists(driver_path):
            driver_service = Service()
        else:
            driver_service = Service(executable_path=driver_path)
    except Exception:
        driver_service = Service()

    # 3. 启动Edge浏览器
    driver = webdriver.Edge(service=driver_service, options=edge_options)
    driver.maximize_window()

    try:
        # 4. 访问目标页面，等待加载完成
        print(f"\n✅ 正在访问目标页面：{target_url}")
        driver.get(target_url)

        # 等待页面基本加载（标题非空即可，适配所有页面）
        WebDriverWait(driver, 20).until(
            lambda d: d.title != ""
        )
        print(f"✅ 页面加载完成，Burp 可捕获所有流量（包括手动点击操作）")
        print(f"ℹ️  请在浏览器中完成你的手动点击操作，操作完成后无需关闭浏览器")
        print(f"ℹ️  等待 30 秒后自动开始筛选 Burp 日志（如需延长等待时间，可修改脚本中的 WAIT_TIME 变量）")

    except Exception as e:
        print(f"❌ 自动化操作失败：{str(e)}")
        driver.quit()
        return None

    return driver


# ===================== 第二部分：Burp 日志筛选优化核心逻辑 =====================
def filter_burp_log_for_json(raw_log_content):
    """
    核心函数：筛选原始 Burp 日志中 含目标 URL + 白名单 Content-Type + 有效 JSON 返回体 的流量条目
    关键：1. 仅保留包含目标 URL 的流量 2. 完整保留请求头、响应头及 JSON 返回体
    :param raw_log_content: 原始 Burp 日志内容
    :return: 筛选后的纯净日志内容
    """
    # Burp 日志默认分隔符（用于拆分单个流量条目）
    traffic_separator = "======================================================"
    # 拆分所有流量条目
    traffic_entries = raw_log_content.split(traffic_separator)
    # 存储筛选后的有效条目
    valid_entries = []

    # 正则匹配完整 JSON 块（支持跨行、含空格）
    json_block_pattern = r'\{[\s\S]*?\}'
    # 补充匹配数组格式 JSON（可选，若有 [] 格式的返回体）
    json_array_pattern = r'\[[\s\S]*?\]'

    print(f"\n🔍 开始解析日志，共检测到 {len(traffic_entries)} 条原始流量条目...")
    print(f"📋 白名单规则：仅保留 {WHITELIST_CONTENT_TYPE} 类型流量")
    print(f"🔗 URL 匹配规则：仅保留包含 '{TARGET_URL_KEYWORD}' 的流量（大小写不敏感）")
    print(f"📌 配置说明：完整保留请求头、响应头及 JSON 返回体")

    for entry in traffic_entries:
        # 关键：不提前 strip 整个 entry，仅用于判断空条目（避免丢失请求头的格式和空格）
        entry_original = entry  # 保留原始条目（含格式、空格），确保请求头完整
        entry_stripped = entry_original.strip()

        # 跳过空条目
        if not entry_stripped:
            continue

        # 步骤 1：URL 匹配筛选——仅保留包含目标 URL 关键字的流量（大小写不敏感兼容）
        if TARGET_URL_KEYWORD.lower() not in entry_original.lower():
            continue

        # 步骤 2：核心白名单筛选——仅保留包含指定 Content-Type 的流量
        if WHITELIST_CONTENT_TYPE.lower() not in entry_original.lower():
            continue

        # 步骤 3：初步过滤——判断是否包含 JSON 特征字符
        if '{"' not in entry_original and '}' not in entry_original and '[' not in entry_original and ']' not in entry_original:
            continue

        # 步骤 4：提取所有可能的 JSON 候选片段
        json_candidates = re.findall(json_block_pattern, entry_original, re.DOTALL)
        json_candidates += re.findall(json_array_pattern, entry_original, re.DOTALL)
        valid_json_found = False

        # 步骤 5：验证候选片段是否为合法 JSON
        for candidate in json_candidates:
            candidate_stripped = candidate.strip()
            # 过滤过短的无效片段
            if len(candidate_stripped) < MIN_JSON_LENGTH:
                continue

            # 尝试解析 JSON（处理常见格式问题：末尾多余逗号、分号、括号）
            try:
                # 简单修复不规范 JSON
                fixed_candidate = candidate_stripped.rstrip(',').rstrip(';').rstrip(')').rstrip('}')
                # 补全缺失的闭合符（简单场景）
                if fixed_candidate.count('{') > fixed_candidate.count('}'):
                    fixed_candidate += '}' * (fixed_candidate.count('{') - fixed_candidate.count('}'))
                if fixed_candidate.count('[') > fixed_candidate.count(']'):
                    fixed_candidate += ']' * (fixed_candidate.count('[') - fixed_candidate.count(']'))

                # 验证合法性
                json.loads(fixed_candidate)
                valid_json_found = True
                break
            except json.JSONDecodeError:
                continue

        # 步骤 6：保留有效条目（完整保留请求头+响应头+JSON，不修改原始格式）
        if valid_json_found:
            if PRESERVE_TRAFFIC_CONTEXT:
                valid_entries.append(entry_original)
            else:
                # 仅保留纯 JSON 内容（如需此模式，可将 PRESERVE_TRAFFIC_CONTEXT 改为 False）
                pure_json = "\n".join([c for c in json_candidates if len(c.strip()) >= MIN_JSON_LENGTH])
                valid_entries.append(pure_json)

    # 步骤 7：重组筛选后的日志（还原分隔符，保持格式清晰）
    filtered_log = traffic_separator.join(valid_entries)
    print(f"✅ 日志筛选完成，共保留 {len(valid_entries)} 条符合条件的有效 JSON 流量条目")
    return filtered_log


def run_json_log_filter():
    """运行完整的日志过滤流程：读取 → 筛选 → 导出"""
    try:
        # 1. 读取原始 Burp 日志文件
        print(f"\n📂 正在读取原始日志文件：{RAW_BURP_LOG_PATH}")
        with open(RAW_BURP_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            raw_log_content = f.read()

        if not raw_log_content.strip():
            print("❌ 原始日志文件为空，无法进行筛选")
            return

        # 2. 执行 JSON 流量筛选
        filtered_log_content = filter_burp_log_for_json(raw_log_content)

        # 3. 生成带时间戳的导出文件名（避免覆盖）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url_keyword = TARGET_URL_KEYWORD.replace('/', '_').replace(':', '').replace('\\', '_')
        export_filename = f"{EXPORT_DIR}burp_url_match_{safe_url_keyword}_application_json_{timestamp}.log"

        # 4. 导出筛选后的日志文件
        with open(export_filename, "w", encoding="utf-8") as f:
            f.write(filtered_log_content)

        print(f"📤 筛选后的日志已导出：{os.path.abspath(export_filename)}")
        print(f"🎉 整个日志过滤流程完成！")

    except FileNotFoundError:
        print(f"❌ 未找到原始日志文件，请检查路径是否正确：{RAW_BURP_LOG_PATH}")
    except Exception as e:
        print(f"❌ 过滤流程出现异常：{str(e)}")


# ===================== 第三部分：流程整合（访问页面 → 手动操作 → 筛选日志）=====================
if __name__ == "__main__":
    # 步骤 1：打印流程标题
    print("=" * 80)
    print("  Selenium + Burp 日志筛选 整合工具")
    print("=" * 80)

    # 步骤 2：启动 Selenium，访问目标页面
    driver = selenium_burp_automation_edge(TARGET_URL, BURP_PROXY)

    # 步骤 3：等待手动操作完成（可修改等待时间，默认 30 秒）
    WAIT_TIME = 30  # 手动操作的预留时间（秒）
    time.sleep(WAIT_TIME)

    # 步骤 4：执行 Burp 日志筛选（无论浏览器是否关闭，都执行筛选）
    print("\n" + "=" * 60)
    print("  开始执行 Burp 日志 JSON 提取（URL 匹配 + 白名单版）")
    print("=" * 60)
    run_json_log_filter()

    # 步骤 5：保持浏览器打开（如需操作完成后自动关闭，可注释下面的循环）
    if driver:
        print(f"\nℹ️  日志筛选已完成，浏览器将保持打开状态，你可继续操作，关闭浏览器后脚本结束")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print(f"\nℹ️  检测到手动终止，关闭浏览器...")
            driver.quit()