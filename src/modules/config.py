import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(PROJECT_ROOT)  # 项目的根目录
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
HISTORY_DIR = os.path.join(PROJECT_ROOT, "history")
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "screenshots")
PROMPT_FILE = os.path.join(ROOT_DIR, "提示词.md")

DEFAULT_LLM_PROMPT = "请提取图片中的课程信息并按格式返回"

DEFAULT_CONFIG = {
    "llm_api_key": "",
    "llm_api_base": "https://api.siliconflow.cn/v1",
    "llm_model": "Qwen/Qwen3.6-27B",
    "llm_temperature": 0.1,
    "notification_template": "",
    "theme": "light",
    "save_history": True,
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


def save_config(cfg):
    from loguru import logger
    ensure_dirs()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise


def get_prompt_from_file():
    """从提示词.md文件读取提示词"""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return DEFAULT_LLM_PROMPT


def update_prompt_template(template_text):
    """更新提示词文件中的通知模板示例部分
    
    处理逻辑：
    1. 解析用户模板，分离课程行和页脚文字
    2. 更新 Output Format 部分
    3. 更新示例部分
    """
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析模板，分离课程行和页脚文字
        separator = "━━━━━━━━━━━━━━━━━━"
        lines = template_text.strip().split("\n")
        
        course_lines = []
        footer_lines = []
        found_last_separator = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == separator:
                if found_last_separator:
                    # 第二个分隔线之后的内容是页脚
                    footer_lines = [l.strip() for l in lines[i+1:] if l.strip()]
                    break
                else:
                    found_last_separator = True
                    course_lines.append(stripped)
            elif not found_last_separator:
                # 分隔线之前的内容（包括标题）
                course_lines.append(stripped)
            else:
                # 两个分隔线之间的内容（课程行）
                course_lines.append(stripped)
        
        # 确保有页脚文字
        if not footer_lines:
            footer_lines = ["此条信息不用回复，如有特殊情况提前沟通"]
        
        # 构建标准模板格式
        footer_text = "\n".join(footer_lines)
        
        # 构建 Output Format 部分
        output_format = f"""# Output Format (重要)
请直接按照以下通知格式输出，**不要返回JSON**，直接输出格式化后的通知文本。

如果有多门课程，每门课程占一行，格式如下：
📚 课程通知
━━━━━━━━━━━━━━━━━━
📅 日期：X月X日 周X | 📖 科目：XXX | ⏰ 时间：HH:MM-HH:MM（上午/下午/晚上） | 📍 位置：XXX
📅 日期：X月X日 周X | 📖 科目：XXX | ⏰ 时间：HH:MM-HH:MM（上午/下午/晚上） | 📍 位置：XXX
📅 日期：X月X日 周X | 📖 科目：XXX | ⏰ 时间：HH:MM-HH:MM（上午/下午/晚上） | 📍 位置：XXX
━━━━━━━━━━━━━━━━━━
{footer_text}"""
        
        # 构建示例部分（保留用户自定义的课程行）
        example_section = f"""# 示例（假设截图中有3门课）

{template_text}"""
        
        # 更新 Output Format 部分
        output_format_marker = "# Output Format"
        example_marker = "# 示例"
        
        output_start = content.find(output_format_marker)
        example_start = content.find(example_marker)
        
        if output_start >= 0 and example_start > output_start:
            new_content = (
                content[:output_start] +
                output_format + "\n\n" +
                example_section + "\n\n" +
                content[example_start + len(example_marker):]
            )
        else:
            # 如果结构不符合预期，只更新示例部分
            workflow_marker = "# Workflow"
            workflow_start = content.find(workflow_marker)
            
            if workflow_start >= 0:
                new_content = (
                    content[:workflow_start] +
                    example_section + "\n\n" +
                    content[workflow_start:]
                )
            else:
                new_content = content + f"\n\n{example_section}\n"
        
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        from loguru import logger
        logger.info("已更新提示词模板")
        
    except Exception as e:
        from loguru import logger
        logger.error(f"更新提示词模板失败: {e}")
        raise
