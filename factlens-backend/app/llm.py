"""大模型调用层。
- 有 LLM_API_KEY 时：走 OpenAI 兼容接口（智谱 / DeepSeek / 豆包 / Kimi / OpenAI 都兼容）。
- 没有 key 时：本模块所有函数返回 None，上层会自动用“搜索 + 规则”降级，也能跑。
"""

import json

import requests

from .config import config

_TIMEOUT = 60


class LLMUnavailable(Exception):
    """没有配置可用的模型 key。"""


def available() -> bool:
    return bool(config.LLM_API_KEY)


def _chat(messages: list[dict], temperature: float = 0.2, max_tokens: int = 1200) -> str:
    if not available():
        raise LLMUnavailable()
    payload = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(
        f"{config.LLM_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=_TIMEOUT,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"LLM 请求失败: HTTP {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _chat_json(messages: list[dict], temperature: float = 0.2, max_tokens: int = 2000) -> dict:
    """要求模型输出 JSON，并尝试解析。"""
    content = _chat(messages, temperature=temperature, max_tokens=max_tokens)
    content = content.strip()
    # 去掉可能的 ```json 围栏
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"模型未返回 JSON: {content[:200]}")
    return json.loads(content[start : end + 1])


def decompose_claims(text: str) -> list[str] | None:
    """把用户输入的说法拆成 1~3 条可单独核查的断言。无 key 返回 None。"""
    if not available():
        return None
    prompt = (
        "你是信息核查系统的断言拆解器。请把下面这段待核查的信息，拆成 1~3 条"
        "独立、具体、可被搜索引擎验证的断言（每条尽量是一句可判断真假的陈述）。"
        "只输出 JSON，格式：{\"claims\": [\"断言1\", \"断言2\", ...]}。不要输出其他内容。\n\n"
        f"待核查信息：{text}"
    )
    try:
        data = _chat_json([{"role": "user", "content": prompt}], temperature=0.1)
        claims = data.get("claims", [])
        return [c for c in claims if isinstance(c, str) and c.strip()][:3] or None
    except Exception:
        return None


def judge(text: str, claims_evidence: list[dict]) -> dict | None:
    """综合所有断言的证据，给出整体结论。无 key 返回 None。
    claims_evidence: [{"claim": str, "sources": [{title,url,snippet,domain}]}]
    """
    if not available():
        return None
    evidence_text = json.dumps(claims_evidence, ensure_ascii=False, indent=1)
    prompt = (
        "你是严谨的信息核查员。根据下面的待核查信息，以及为每条断言检索到的网页证据，"
        "给出一个整体核查结论。结论只能是以下四种之一：\n"
        "- 确认属实\n- 确认不实\n- 部分属实\n- 暂无法核实\n"
        "判定原则：只依据证据；证据不足就写“暂无法核实”，绝不编造；"
        "要区分“来源本身是官方/权威”与“一般网页”。\n"
        "只输出 JSON，格式：\n"
        "{\n"
        '  "conclusion": "确认属实/确认不实/部分属实/暂无法核实",\n'
        '  "summary": "整体分析摘要，80字左右",\n'
        '  "reason": "分析理由，说明依据了哪些证据、为什么这么判",\n'
        '  "support": ["支持该结论的证据要点", "..."],\n'
        '  "against": ["反驳该结论的证据要点", "..."],\n'
        '  "uncertainties": ["不确定因素或需要进一步核实的点", "..."]\n'
        "}\n\n"
        f"待核查信息：{text}\n\n检索到的证据：{evidence_text}"
    )
    try:
        data = _chat_json([{"role": "user", "content": prompt}], temperature=0.2)
        allowed = {"确认属实", "确认不实", "部分属实", "暂无法核实"}
        if data.get("conclusion") not in allowed:
            data["conclusion"] = "暂无法核实"
        return data
    except Exception:
        return None
