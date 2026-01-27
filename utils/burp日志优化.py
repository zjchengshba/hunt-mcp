import json
import re
from datetime import datetime
from config import BURP_LOG_PATH

# ===================== 工具配置（可根据需求修改）=====================
# 1. 原始 Burp 日志路径（输入文件）
RAW_BURP_LOG_PATH = BURP_LOG_PATH  # 原始日志文件（Burp 自动保存的日志）
# 2. 筛选后日志导出路径（输出文件，自动带时间戳，避免覆盖）
EXPORT_DIR = "./"
# 3. 筛选配置（可微调）
MIN_JSON_LENGTH = 5  # 最小 JSON 片段长度，过滤无意义的短片段（如 {}、{"k":""}）
PRESERVE_TRAFFIC_CONTEXT = True  # 保持为 True，确保完整保留请求头+响应头+JSON 返回体
# 4. 核心白名单：仅保留该 Content-Type 的流量
WHITELIST_CONTENT_TYPE = "Content-Type: application/json"
# 5. 新增：URL 匹配参数（仅保留包含该 URL 关键字的流量，支持完整 URL 或路径片段，大小写不敏感）
# 示例1：完整 URL → "https://dipp.sf-express.com/api"
# 示例2：路径片段 → "/api"、"/user/info"
TARGET_URL_KEYWORD = "eva2.csdn.net"  # 可根据需求修改为你的目标 URL/路径


# ===================== 核心过滤逻辑（白名单模式 + URL 匹配 + 完整保留请求头）=====================
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

    print(f"🔍 开始解析日志，共检测到 {len(traffic_entries)} 条原始流量条目...")
    print(f"📋 白名单规则：仅保留 {WHITELIST_CONTENT_TYPE} 类型流量")
    print(f"🔗 URL 匹配规则：仅保留包含 '{TARGET_URL_KEYWORD}' 的流量（大小写不敏感）")
    print(f"📌 配置说明：完整保留请求头、响应头及 JSON 返回体")

    for entry in traffic_entries:
        # 关键：不提前 strip 整个 entry，仅用于判断空条目（避免丢失请求头的格式和空格）
        entry_original = entry  # 保留原始条目（含格式、空格），确保请求头完整
        entry_stripped = entry_original

        # 跳过空条目
        if not entry_stripped:
            continue

        # 步骤 1：新增 URL 匹配筛选——仅保留包含目标 URL 关键字的流量（大小写不敏感兼容）
        if TARGET_URL_KEYWORD.lower() not in entry_original.lower():
            continue

        # 步骤 2：核心白名单筛选——仅保留包含指定 Content-Type 的流量（大小写不敏感兼容）
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
                # 关键：添加原始条目（entry_original），而非 stripped 后的条目，确保请求头完整无丢失
                valid_entries.append(entry_original)
            else:
                # 仅保留纯 JSON 内容（如需此模式，可将 PRESERVE_TRAFFIC_CONTEXT 改为 False）
                pure_json = "\n".join([c for c in json_candidates if len(c.strip()) >= MIN_JSON_LENGTH])
                valid_entries.append(pure_json)

    # 步骤 7：重组筛选后的日志（还原分隔符，保持格式清晰，请求头完整）
    filtered_log = traffic_separator.join(valid_entries)
    print(f"✅ 日志筛选完成，共保留 {len(valid_entries)} 条符合 URL 匹配+白名单的有效 JSON 流量条目")
    return filtered_log


# ===================== 文件读写与导出（无需修改）=====================
def run_json_log_filter():
    """运行完整的日志过滤流程：读取 → 筛选 → 导出"""
    try:
        # 1. 读取原始 Burp 日志文件
        print(f"📂 正在读取原始日志文件：{RAW_BURP_LOG_PATH}")
        with open(RAW_BURP_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            raw_log_content = f.read()

        if not raw_log_content.strip():
            print("❌ 原始日志文件为空，无法进行筛选")
            return

        # 2. 执行 JSON 流量筛选（URL 匹配 + 白名单模式 + 完整保留请求头）
        filtered_log_content = filter_burp_log_for_json(raw_log_content)

        # 3. 生成带时间戳的导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 文件名添加 url_match 标识，方便区分
        export_filename = f"{EXPORT_DIR}burp_url_match_{TARGET_URL_KEYWORD.replace('/', '_').replace(':', '')}_application_json_{timestamp}.log"

        # 4. 导出筛选后的日志文件
        with open(export_filename, "w", encoding="utf-8") as f:
            f.write(filtered_log_content)

        print(f"📤 筛选后的日志已导出：{export_filename}")
        print(f"🎉 整个过滤流程完成，日志完整保留请求头、响应头及 JSON 返回体")

    except FileNotFoundError:
        print(f"❌ 未找到原始日志文件，请检查路径是否正确：{RAW_BURP_LOG_PATH}")
    except Exception as e:
        print(f"❌ 过滤流程出现异常：{str(e)}")


# ===================== 运行工具（直接执行即可）=====================
if __name__ == "__main__":
    print("=" * 60)
    print("  Burp 日志 JSON 提取工具（URL 匹配 + 白名单版 + 完整保留请求头）")
    print("=" * 60)
    run_json_log_filter()