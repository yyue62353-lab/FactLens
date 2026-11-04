"""智能体编排：拆解断言 -> 联网检索证据 -> 判定 -> 生成核查报告。

有 key 时用大模型拆解和判定；没有 key 时自动降级为“搜索 + 启发式规则”，
保证整个流程也能跑通、能演示（结论会偏保守，多数标为“暂无法核实”）。
"""

import re
import datetime

from . import llm, searcher

# 四种结论类型（与前端一致）
TYPE_MAP = {
    "确认属实": "true",
    "确认不实": "false",
    "部分属实": "partial",
    "暂无法核实": "unknown",
}

# 权威域名关键词（用于降级判定时给来源加权）
_AUTHORITY_HINTS = (
    "gov.cn", "edu.cn", "mfa.gov", "cctv", "people.com.cn", "xinhuanet",
    "baike", "wikipedia", "who.int", "un.org", "moj.gov", "moe.gov",
)

# 支持 / 反驳 的方向性关键词
_SUPPORT_WORDS = ("确认", "属实", "确实", "免费", "存在", "符合", "规定", "官方", "证实", "支持")
_AGAINST_WORDS = ("不实", "谣言", "辟谣", "不属实", "假的", "误导", "否认", "澄清", "没有", "并非", "不符")


def _now() -> str:
    # 固定使用北京时间（UTC+8），避免服务器默认 UTC 导致时间差 8 小时
    bj_tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M")


def _clean_claims(text: str) -> list[str]:
    """无 key 时用规则把输入切成 1~3 条较完整的句子作为断言。"""
    sentences = [s.strip() for s in re.split(r"[。！？!?；;]", text) if s.strip()]
    sentences = [s for s in sentences if 6 <= len(s) <= 60]
    return sentences[:3] or ([text.strip()[:60]] if text.strip() else [])


def _judge_no_llm(text: str, claims_evidence: list[dict]) -> dict:
    """无 key 时的保守判定：只采信与断言“真正相关”的来源，拿不准就标无法核实。"""
    def is_relevant(s: dict, claim: str) -> bool:
        words = [w for w in re.split(r"[\s，。！？!?、：:；;（）()“”\"'0-9一二三四五六七八九十]+", claim)
                 if 2 <= len(w) <= 10]
        if not words:
            return True
        blob = (s.get("title", "") + " " + s.get("snippet", "")).lower()
        return sum(1 for w in words if w in blob) >= 2

    relevant = []
    authority_relevant = 0
    support_hits = against_hits = 0
    for ce in claims_evidence:
        claim = ce.get("claim", "")
        for s in ce.get("sources", []):
            if not is_relevant(s, claim):
                continue
            relevant.append(s)
            blob = (s.get("title", "") + " " + s.get("snippet", "") + " " + s.get("domain", "")).lower()
            if any(h in blob for h in _AUTHORITY_HINTS):
                authority_relevant += 1
            if any(w in blob for w in _SUPPORT_WORDS):
                support_hits += 1
            if any(w in blob for w in _AGAINST_WORDS):
                against_hits += 1

    if len(relevant) == 0:
        conclusion = "暂无法核实"
    elif authority_relevant >= 2 and support_hits > against_hits:
        conclusion = "部分属实" if against_hits > 0 else "确认属实"
    elif authority_relevant >= 2 and against_hits > support_hits:
        conclusion = "确认不实"
    elif len(relevant) >= 4 and support_hits >= 3 and support_hits > against_hits:
        conclusion = "部分属实"
    else:
        conclusion = "暂无法核实"

    return {
        "conclusion": conclusion,
        "summary": (
            f"系统将内容拆解为 {len(claims_evidence)} 条断言并检索网页证据，"
            f"共检索到 {sum(len(ce.get('sources', [])) for ce in claims_evidence)} 条来源，"
            f"其中与断言直接相关 {len(relevant)} 条（权威来源 {authority_relevant} 条）。"
            "当前未配置大模型 key，采用保守判定，详细结论建议配置大模型后复核。"
        ),
        "reason": (
            "证据不足或方向不明确时，不做“确属真/假”的强判定；"
            "只有出现多条相关权威来源且方向一致时才给出倾向性结论。"
        ),
        "support": ["检索到与待核查信息相关的来源若干，可作为进一步核实的起点。"],
        "against": ["当前证据不足以给出强否定结论，需人工复核或配置大模型后加深分析。"],
        "uncertainties": [
            "未配置大模型 key，判定为启发式规则，准确性有限。",
            "建议补充权威信源逐条核实。",
        ],
    }


def _dedup_sources(sources: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for s in sources:
        url = s.get("url", "")
        if url and url not in seen:
            seen.add(url)
            out.append(s)
    return out


def check(text: str) -> dict:
    """完整核查流程，返回与前端 /api/check 约定的 JSON 结构。"""
    text = (text or "").strip()
    if not text:
        raise ValueError("待核查内容不能为空")

    # 1) 拆解断言
    if llm.available():
        claims = llm.decompose_claims(text)
    else:
        claims = None
    claims = claims or _clean_claims(text)
    if not claims:
        claims = [text[:60]]

    # 2) 逐条检索证据
    claims_evidence = []
    for claim in claims:
        ce = searcher.search_assertion(claim)
        claims_evidence.append({"claim": claim, "sources": ce["sources"]})

    # 3) 判定
    if llm.available():
        judgment = llm.judge(text, claims_evidence)
    else:
        judgment = None
    judgment = judgment or _judge_no_llm(text, claims_evidence)

    conclusion = judgment.get("conclusion", "暂无法核实")

    # 4) 汇总全部来源
    all_sources = _dedup_sources([s for ce in claims_evidence for s in ce.get("sources", [])])

    return {
        "conclusion": conclusion,
        "conclusion_type": TYPE_MAP.get(conclusion, "unknown"),
        "summary": judgment.get("summary", ""),
        "reason": judgment.get("reason", ""),
        "support": judgment.get("support", []),
        "against": judgment.get("against", []),
        "uncertainties": judgment.get("uncertainties", []),
        "claims": claims_evidence,
        "sources": all_sources,
        "checked_at": _now(),
        "used_llm": llm.available(),
    }
