"""FactLens 后端配置。
支持从项目根目录的 .env 文件读取，也支持直接用环境变量。
"""

import os
from pathlib import Path


def _load_dotenv() -> None:
    """简单解析项目根目录的 .env 文件（不依赖第三方库）。"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        text = env_path.read_text(encoding="utf-8")
    except Exception:
        text = env_path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


class Config:
    # ---- 大模型（OpenAI 兼容接口）----
    # 有 key 就走真 AI；没有 key 时后端会自动降级为“搜索 + 规则判定”，也能跑。
    LLM_API_KEY = _get("LLM_API_KEY")
    # 兼容智谱 / DeepSeek / 豆包 / Kimi / OpenAI 等
    LLM_BASE_URL = _get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    LLM_MODEL = _get("LLM_MODEL", "glm-4.7-flash")

    # ---- 搜索 ----
    SEARCH_RESULTS_PER_CLAIM = int(_get("SEARCH_RESULTS_PER_CLAIM", "4"))

    # ---- 服务 ----
    HOST = _get("HOST", "0.0.0.0")
    PORT = int(_get("PORT", "8000"))


config = Config()
