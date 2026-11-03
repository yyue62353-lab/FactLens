"""Vercel 无服务器入口：把 FastAPI 应用暴露为 ASGI app。

Vercel 的 Python Runtime 会检测本文件中的 app 变量（ASGI 应用），
所有请求经 vercel.json 的 rewrites 转发到这里，再由 FastAPI 内部路由处理。
"""

from app.main import app
