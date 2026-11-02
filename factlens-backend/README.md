# FactLens 智能体后端

用户输入一个说法 → 拆解成可核查的断言 → 联网检索证据 → AI 判定真伪（属实/不实/部分属实/无法核实）→ 返回带证据链的核查报告。

## 目录结构
```
factlens-backend/
├── app/
│   ├── main.py       # FastAPI 服务入口，提供 POST /api/check
│   ├── agent.py      # 智能体编排：拆解→检索→判定→报告
│   ├── llm.py        # 大模型调用（智谱/DeepSeek/豆包/Kimi/OpenAI 通用）
│   ├── searcher.py   # 必应联网检索（免费，无需 key）
│   └── config.py     # 配置（自动读取 .env）
├── requirements.txt
├── .env.example      # 配置示例（复制为 .env 填写）
└── .gitignore        # 已排除 .env（含密钥，勿提交）
```

## 本地运行
```bash
pip install -r requirements.txt
# 复制 .env.example 为 .env 并填入 LLM_API_KEY（不填也能跑，但会降级为保守规则）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 健康检查：`GET http://localhost:8000/api/health`
- 核查接口：`POST http://localhost:8000/api/check`，请求体 `{"text": "待核查内容"}`
- 接口文档：`http://localhost:8000/docs`

## 大模型 key（强烈建议配置）
没有 key 时后端自动降级为“搜索 + 规则判定”（也能跑，但结论偏保守）。
推荐**智谱 GLM 免费模型**：
1. 打开 https://open.bigmodel.cn 用手机号注册登录
2. 左侧「API 密钥」→ 创建 → 复制 `sk-` 开头的 key
3. 无需充值，免费模型直接可用
4. 填入 `.env` 的 `LLM_API_KEY`，重启后端

## 部署上线（Render 免费）
1. 把后端代码（整个 `factlens-backend` 目录）推到你团队的 GitHub 仓库
2. 到 https://render.com 用 GitHub 登录 → New + → Web Service → 选择仓库
3. 配置：
   - Root Directory：`factlens-backend`
   - Build Command：`pip install -r requirements.txt`
   - Start Command：`uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Instance Type：Free
4. Environment 添加变量：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`
5. Deploy 后得到 `https://xxx.onrender.com` 公网地址
6. 前端构建时设置 `VITE_API_BASE` 指向该地址并重新部署

> 免费实例闲置 15 分钟会休眠，演示前先访问一次后端地址（约 30 秒冷启动）唤醒。
