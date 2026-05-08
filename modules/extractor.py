import json
import base64
import io
import httpx
from loguru import logger
from PIL import Image

from .config import get_prompt_from_file


def _pil_to_base64(pil_image: Image.Image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _safe_val(val, fallback=""):
    return (val or "").strip() or fallback


def _infer_period(start_time):
    if not start_time:
        return ""
    try:
        h = int(start_time.split(":")[0])
        if h < 12:
            return "上午"
        elif h < 18:
            return "下午"
        return "晚上"
    except Exception:
        return ""


def _fill_template(template: str, course: dict) -> str:
    period = course.get("period", "")
    if not period:
        period = _infer_period(course.get("start_time", ""))

    values = {
        "date": _safe_val(course.get("date")),
        "course_name": _safe_val(course.get("course_name")),
        "start_time": _safe_val(course.get("start_time")),
        "end_time": _safe_val(course.get("end_time")),
        "period": _safe_val(period),
        "location": _safe_val(course.get("location")),
        "notes": _safe_val(course.get("notes")),
    }

    result = template
    for key, val in values.items():
        result = result.replace("「" + key + "」", val).replace("{" + key + "}", val)
    return result


def _create_client(config: dict, timeout=120):
    api_key = config.get("llm_api_key", "").strip()
    api_base = config.get("llm_api_base", "").strip().rstrip("/")
    if not api_key or not api_base:
        raise ValueError("API Key、API Base 不能为空，请在设置中配置")
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=api_base, timeout=timeout,
                  http_client=httpx.Client(proxy=None, follow_redirects=True))


def _parse_vlm_response(content: str) -> list:
    # 尝试清理常见的包装标记
    cleaned = content.strip()
    
    # 移除可能的代码块标记
    if cleaned.startswith("```"):
        # 移除开头的```和可能的语言标记
        first_newline = cleaned.find("\n")
        if first_newline > 0:
            cleaned = cleaned[first_newline + 1:]
        else:
            cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        # 移除结尾的```
        last_newline = cleaned.rfind("\n")
        if last_newline > 0 and last_newline < len(cleaned) - 3:
            cleaned = cleaned[:last_newline]
        else:
            cleaned = cleaned[:-3]
    
    # 尝试直接解析
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # 如果失败，尝试查找JSON部分（从[到]）
        json_start = cleaned.find('[')
        json_end = cleaned.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            try:
                parsed = json.loads(cleaned[json_start:json_end])
            except json.JSONDecodeError:
                # 尝试从{到}（单个对象）
                json_start = cleaned.find('{')
                json_end = cleaned.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        parsed = json.loads(cleaned[json_start:json_end])
                    except json.JSONDecodeError:
                        logger.error(f"VLM 返回无法解析为 JSON: {content[:300]}")
                        return None
                else:
                    logger.error(f"VLM 返回无法解析为 JSON: {content[:300]}")
                    return None
        else:
            # 尝试查找单个对象
            json_start = cleaned.find('{')
            json_end = cleaned.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    parsed = json.loads(cleaned[json_start:json_end])
                except json.JSONDecodeError:
                    logger.error(f"VLM 返回无法解析为 JSON: {content[:300]}")
                    return None
            else:
                logger.error(f"VLM 返回无法解析为 JSON: {content[:300]}")
                return None
    
    if isinstance(parsed, dict):
        parsed = [parsed]
    return parsed if isinstance(parsed, list) else None


def _build_template(config: dict) -> str:
    template = config.get("notification_template", "")
    if not template:
        template = (
            "📚 课程通知\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📅 日期：「date」\n"
            "📖 科目：「course_name」\n"
            "⏰ 时间：「start_time」 - 「end_time」（「period」）\n"
            "📍 位置：「location」\n"
            "📝 备注：「notes」\n"
            "━━━━━━━━━━━━━━━━━━"
        )
    return template


def extract_with_vlm(pil_image: Image.Image, config: dict) -> str:
    """发送单张图片给视觉大模型"""
    # 复用多图片处理逻辑，传入单张图片列表
    return extract_with_vlm_multi([pil_image], config)


def extract_with_vlm_multi(images, config: dict) -> str:
    """多图片处理：分别处理每张图片，然后合并去重"""
    model = config.get("llm_model", "").strip()
    temperature = config.get("llm_temperature", 0.1)
    if not model:
        raise ValueError("模型名称不能为空，请在设置中配置")
    
    prompt = get_prompt_from_file()
    template = _build_template(config)
    
    client = _create_client(config, timeout=180)
    
    all_courses = []
    
    for idx, pil_img in enumerate(images):
        logger.info(f"正在处理第 {idx + 1} 张图片...")
        
        img_b64 = _pil_to_base64(pil_img)
        
        messages = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        ]}]
        
        # 调用模型
        kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=4096)
        try:
            kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
        except Exception:
            logger.warning("JSON mode 不受支持，回退到普通模式")
            kwargs.pop("response_format")
            resp = client.chat.completions.create(**kwargs)
        
        content = resp.choices[0].message.content.strip()
        logger.debug(f"第 {idx + 1} 张图片 VLM 原始返回: {content[:300]}")
        
        parsed = _parse_vlm_response(content)
        if parsed is not None:
            all_courses.extend(parsed)
            logger.info(f"第 {idx + 1} 张图片成功提取 {len(parsed)} 个课程")
        else:
            logger.warning(f"第 {idx + 1} 张图片解析失败，可能未识别到课程信息")
    
    # 去重逻辑：相同日期、时间、科目的课程视为重复
    unique_courses = []
    seen = set()
    for course in all_courses:
        # 创建唯一标识
        key = (
            course.get("date", ""),
            course.get("start_time", ""),
            course.get("end_time", ""),
            course.get("course_name", "")
        )
        if key not in seen:
            seen.add(key)
            unique_courses.append(course)
    
    logger.info(f"共提取 {len(all_courses)} 个课程，去重后剩余 {len(unique_courses)} 个")
    
    if not unique_courses:
        return "未识别到课程信息"
    
    # 按日期和时间排序
    unique_courses.sort(key=lambda x: (
        x.get("date", ""),
        x.get("start_time", "")
    ))
    
    # 填充模板
    results = [_fill_template(template, course) for course in unique_courses]
    return "\n\n".join(results)





def test_api_connectivity(config: dict) -> tuple[bool, str]:
    try:
        api_key = config.get("llm_api_key", "").strip()
        api_base = config.get("llm_api_base", "").strip().rstrip("/")
        model = config.get("llm_model", "").strip()
        if not api_key or not api_base or not model:
            return False, "API Key、API Base 或模型名称为空"
        client = _create_client(config, timeout=30)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "请回复连接成功"}],
            temperature=0.1,
            max_tokens=20,
        )
        msg = resp.choices[0].message.content.strip()
        return True, f"连接成功（{msg}）"
    except Exception as e:
        return False, f"连接失败：{e}"
