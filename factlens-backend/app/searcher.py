"""必应搜索：免费、无需 key，国内可访问。
负责把一条“待核查断言”变成一组来源（标题 + 链接 + 摘要）。
"""

import re
import urllib.parse

import requests

from .config import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class Source:
    """一条检索到的来源。"""

    def __init__(self, title: str, url: str, snippet: str, domain: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.domain = domain or _domain_of(url)

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "domain": self.domain,
        }


def _domain_of(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url or "")
    if not m:
        return ""
    return m.group(1).replace("www.", "")


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _extract_url(href: str) -> str:
    """必应返回的链接常带跳转前缀，还原成真实 URL。"""
    if href.startswith("http") and "bing.com" in href and "url=" in href:
        m = re.search(r"[?&]url=([^&]+)", href)
        if m:
            decoded = urllib.parse.unquote(m.group(1))
            if decoded.startswith("http"):
                return decoded
    return href


def search(query: str, num: int = None) -> list:
    """用必应搜索 query，返回最多 num 条 Source。"""
    num = num or config.SEARCH_RESULTS_PER_CLAIM
    url = "https://cn.bing.com/search?q=" + urllib.parse.quote(query)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
    except Exception:
        return []
    if resp.status_code != 200:
        return []

    html = resp.text
    blocks = re.split(r'<li class="b_algo"', html)[1:]
    results: list[Source] = []
    for block in blocks[: num + 2]:
        m_href = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m_href:
            continue
        url = _extract_url(m_href.group(1))
        title = _clean(m_href.group(2))
        m_snip = re.search(r'<p[^>]*class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</p>', block, re.S) or \
                 re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        snippet = _clean(m_snip.group(1)) if m_snip else ""
        if url and title:
            results.append(Source(title, url, snippet))
        if len(results) >= num:
            break
    return results


def search_assertion(assertion: str) -> dict:
    """对一条断言检索，返回 {query, sources}。"""
    results = search(assertion)
    return {
        "query": assertion,
        "sources": [r.to_dict() for r in results],
    }
