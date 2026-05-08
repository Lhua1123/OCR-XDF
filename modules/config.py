import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(PROJECT_ROOT)  # 项目的根目录
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
HISTORY_DIR = os.path.join(PROJECT_ROOT, "history")
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "screenshots")
PROMPT_FILE = os.path.join(ROOT_DIR, "提示词.md")

DEFAULT_LLM_PROMPT = "请提取图片中的课程信息并按格式返回JSON"

DEFAULT_NOTIFICATION_TEMPLATES = {
    "wechat": (
        "📚 课程通知\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📅 日期：「date」\n"
        "📖 科目：「course_name」\n"
        "⏰ 时间：「start_time」 - 「end_time」（「period」）\n"
        "📍 位置：「location」\n"
        "📝 备注：「notes」\n"
        "━━━━━━━━━━━━━━━━━━"
    ),
}

DEFAULT_CONFIG = {
    "llm_api_key": "",
    "llm_api_base": "https://api.siliconflow.cn/v1",
    "llm_model": "Qwen/Qwen3.6-27B",
    "llm_temperature": 0.1,
    "llm_prompt": DEFAULT_LLM_PROMPT,
    "notification_templates": dict(DEFAULT_NOTIFICATION_TEMPLATES),
    "notification_template": list(DEFAULT_NOTIFICATION_TEMPLATES.values())[0],
    "theme": "light",
    "last_template": "wechat",
    "save_history": True,
    "reference_image_path": "",
}


def ensure_dirs():
    for d in [CONFIG_DIR, HISTORY_DIR, SCREENSHOTS_DIR]:
        os.makedirs(d, exist_ok=True)


def load_config():
    ensure_dirs()
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def get_prompt_from_file():
    """从提示词.md文件读取提示词，如果文件不存在或格式不正确，返回默认提示词"""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查内容是否是JSON，如果是则包装成完整提示词
        content = content.strip()
        if content.startswith("[") and content.endswith("]"):
            # 这是JSON数组格式，需要包装成完整提示词
            prompt_template = """# Role: 智能课程排课信息提取专家

# Task
请分析用户提供的课程表长截图，识别其中的课程安排，并按照指定的JSON格式返回所有课程信息。

# Constraints & Rules (重要)
1. **排除已过期课程**：如果单元格的背景是深灰色（或者显示"日期已过"字样），视为无效，直接跳过该区域的课程，不要提取。
2. **精准日期识别**：必须严格根据顶部的星期/日期列标题来匹配下方的课程内容。注意列与列的对齐，防止因为表格边框导致日期错位（例如不要把5月5日的课误认成5月4日）。
3. **地址处理规范**：课程地点信息较长时（如包含具体路名、校区名），请**只提取最后的"教室编号"**。
   - 错误示例：朝阳新城桂懿路学习中心 X朝阳新城桂懿路VIP203
   - 正确提取：VIP203
4. **时间格式**：start_time和end_time使用 "HH:MM" 格式。period使用"上午/下午/晚上"。
5. **内容完整性**：确保提取所有可见的课程，包括不同周次（如周五、周六）的内容。

# Output Format
请严格返回一个 JSON 数组，每个课程对象包含以下字段：
- date: 上课日期（如"5月4日 周一"）
- course_name: 科目/老师姓名
- start_time: 开始时间（HH:MM）
- end_time: 结束时间（HH:MM）
- period: 上午/下午/晚上
- location: 教室简称（只保留教室编号）
- notes: 备注信息（没有则填空字符串）

示例格式：
{example_json}

现在请分析图片中的课程信息并返回JSON数组。"""
            
            try:
                # 验证JSON格式
                json.loads(content)
                # 使用读取的JSON作为示例
                return prompt_template.format(example_json=content)
            except json.JSONDecodeError:
                return DEFAULT_LLM_PROMPT
        else:
            # 已经是完整提示词，直接返回
            return content
    except Exception:
        return DEFAULT_LLM_PROMPT


def save_config(cfg):
    from loguru import logger
    ensure_dirs()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise