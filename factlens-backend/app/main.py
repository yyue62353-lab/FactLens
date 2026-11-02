"""FactLens 智能体后端服务入口。

启动：uvicorn app.main:app --host 0.0.0.0 --port 8000
接口：POST /api/check  (JSON: {"text": "待核查内容"})
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import config
from . import agent

app = FastAPI(title="FactLens 智能体后端", version="1.0.0")

# 允许前端跨域调用（生产环境可按需收紧域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CheckRequest(BaseModel):
    text: str


class HealthResponse(BaseModel):
    status: str
    used_llm: bool
    model: str


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        used_llm=agent.llm.available(),
        model=config.LLM_MODEL,
    )


@app.post("/api/check")
def check(req: CheckRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="待核查内容不能为空")
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="内容过长，请控制在 2000 字以内")
    try:
        return agent.check(text)
    except Exception as exc:  # 兜底：不让用户看到崩溃页
        raise HTTPException(status_code=500, detail=f"核查过程出错：{exc}")
