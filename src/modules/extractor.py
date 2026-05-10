import json
import base64
import io
import time
import re
import httpx
from loguru import logger
from PIL import Image

from .config import get_prompt_from_file


def _pil_to_base64(pil_image: Image.Image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _create_client(config: dict, timeout=120):
    api_key = config.get("llm_api_key", "").strip()
    api_base = config.get("llm_api_base", "").strip().rstrip("/")
    if not api_key or not api_base:
        raise ValueError("API Key、API Base 不能为空，请在设置中配置")
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=api_base, timeout=timeout,
                  http_client=httpx.Client(proxy=None, follow_redirects=True))


def extract_with_vlm(pil_image: Image.Image, config: dict) -> str:
    """发送单张图片给视觉大模型"""
    return extract_with_vlm_multi([pil_image], config)


def extract_with_vlm_multi(images, config: dict) -> str:
    """多图片处理：分别处理每张图片，合并结果"""
    total_start = time.time()
    
    model = config.get("llm_model", "").strip()
    temperature = config.get("llm_temperature", 0.1)
    if not model:
        raise ValueError("模型名称不能为空，请在设置中配置")
    
    # 获取基础提示词
    base_prompt = get_prompt_from_file()
    
    # 获取用户自定义模板
    notification_template = config.get("notification_template", "").strip()
    
    # 如果有自定义模板，将其作为输出格式要求加入提示词
    if notification_template:
        prompt = base_prompt + "\n\n# 用户自定义通知模板（请严格按照此格式输出）\n" + notification_template
    else:
        prompt = base_prompt
    
    client = _create_client(config, timeout=180)
    
    all_results = []
    
    for idx, pil_img in enumerate(images):
        logger.info(f"正在处理第 {idx + 1} 张图片...")
        
        # 图片转 base64
        t0 = time.time()
        img_b64 = _pil_to_base64(pil_img)
        logger.info(f"  图片转 base64: {time.time() - t0:.2f}s, 大小: {len(img_b64) / 1024:.1f}KB")
        
        messages = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        ]}]
        
        # 调用模型
        kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=4096)
        try:
            t0 = time.time()
            resp = client.chat.completions.create(**kwargs)
            api_time = time.time() - t0
            logger.info(f"  API 调用耗时: {api_time:.2f}s")
        except Exception as e:
            logger.error(f"调用模型失败: {e}")
            raise
        
        content = resp.choices[0].message.content.strip()
        logger.debug(f"第 {idx + 1} 张图片返回: {content[:500]}")
        
        if content:
            all_results.append(content)
            logger.info(f"第 {idx + 1} 张图片处理完成")
        else:
            logger.warning(f"第 {idx + 1} 张图片未返回内容")
    
    # 合并结果
    t0 = time.time()
    if not all_results:
        result = "未识别到课程信息"
    else:
        result = _merge_multi_image_results(all_results)
    
    total_time = time.time() - total_start
    logger.info(f"总处理耗时: {total_time:.2f}s")
    
    return result


def _get_date_sort_key(line: str) -> tuple:
    """从课程行中提取日期用于排序
    
    格式：📅 日期：5月5日 周一 | 📖 科目：数学 | ...
    返回 (月, 日) 用于排序
    """
    # 匹配 "X月X日" 格式
    match = re.search(r'(\d+)月(\d+)日', line)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        return (month, day)
    # 如果没有匹配到日期，返回一个很大的值使其排在最后
    return (99, 99)


def _merge_multi_image_results(results: list) -> str:
    """合并多张图片的识别结果
    
    简化逻辑：直接按行解析，识别课程行进行排序和去重
    """
    if not results:
        return "未识别到课程信息"
    
    # 如果只有一张图片，直接返回（模型已按用户模板格式返回）
    if len(results) == 1:
        return results[0]
    
    # 多张图片：解析并合并
    course_lines = []
    seen_courses = set()
    separator = "━━━━━━━━━━━━━━━━━━"
    
    # 课程行的特征：包含 "📅" 和 "|"
    for result in results:
        for line in result.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            # 判断是否是课程行
            if "📅" in stripped and "|" in stripped:
                if stripped not in seen_courses:
                    seen_courses.add(stripped)
                    course_lines.append(stripped)
    
    if not course_lines:
        return results[0]  # 如果没有识别到课程行，返回第一个结果
    
    # 按日期排序课程行
    course_lines.sort(key=_get_date_sort_key)
    
    # 使用第一个结果作为模板，替换课程行部分
    template_lines = results[0].split("\n")
    result_lines = []
    courses_inserted = False
    
    for line in template_lines:
        stripped = line.strip()
        # 在第一个分隔符后插入排序后的课程行
        if stripped == separator and not courses_inserted:
            result_lines.append(line)
            for course in course_lines:
                result_lines.append(course)
            courses_inserted = True
        # 跳过原始的课程行（已在上面插入）
        elif "📅" in stripped and "|" in stripped:
            continue
        else:
            result_lines.append(line)
    
    return "\n".join(result_lines)


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
