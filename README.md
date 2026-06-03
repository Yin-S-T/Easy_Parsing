# Easy Parsing

Easy Parsing 是一个面向科研人员的 AI 辅助论文发现、筛选与初步理解工具。当前版本已经从早期 MVP 规划演进为 **FastAPI 后端 + Next.js 前端** 的 Web 应用：以后端拉取 arXiv 元数据，基于用户研究画像进行规则评分，可选调用 DeepSeek 对候选论文进行复评，并把阅读状态与导出结果保存在本地文件中。

## 当前定位

Easy Parsing 目前更接近个人“研究雷达”，而不是完整的文献数据库或生产级知识库。它适合帮助用户每天快速回答：

- 最近 arXiv 上有哪些论文和我的方向相关？
- 哪些论文应该优先读？
- 推荐理由、证据和风险分别是什么？
- 哪些论文已经保存、稍后读、已读或忽略？
- 如何把本次筛选结果导出为 Markdown、JSON 或 BibTeX？

当前系统不解析全文 PDF，不维护数据库，不做全量 arXiv 镜像，不提供登录权限系统，也没有真正的长期个性化学习。

## 当前功能

- 从 arXiv 拉取近期论文元数据。
- 支持按 arXiv 分类、自由查询词、时间范围和最大数量检索。
- 支持 arXiv 分页拉取、短期本地缓存和去重，减少重复请求与第一页漏检。
- 根据标题、摘要、研究兴趣、正向关键词、排除词、方法信号、分类匹配、论文类型风险和新鲜度进行规则评分。
- 支持可选 DeepSeek 复评，对排名靠前或不确定的候选论文进行语义判断。
- 前端支持英文和中文界面。
- 前端支持 arXiv 分类多选、核心 CS 分类预设和检索参数校验。
- 支持阅读状态：`unread`、`saved`、`read_later`、`read`、`ignored`。
- 支持把论文保存为知识库条目，记录标签、关键收获和研究笔记。
- 支持导出到 `data/exports/`，格式包括 Markdown、JSON、BibTeX。
- 前端包含 Research Radar、Discover、Library、Notes/Knowledge Base、论文详情页，以及预留的 Alerts、Analytics 入口。

## 项目结构

```text
Eassy Parsing/
|-- api.py                         FastAPI 应用入口与 API 路由
|-- requirements.txt               Python 后端依赖
|-- setup_venv.ps1                 Windows PowerShell 环境初始化脚本
|-- setup_venv.bat                 Windows 批处理环境初始化脚本
|-- README.md                      项目说明与使用方式
|-- ARCHITECTURE.md                架构说明与路线建议
|-- src/
|   |-- arxiv_client.py            arXiv Atom API 客户端
|   |-- deepseek_client.py         可选 DeepSeek 论文复评层
|   |-- i18n.py                    arXiv 分类、部分文案、关键词拆分工具
|   |-- models.py                  Paper、Recommendation、ScoreBreakdown 数据模型
|   |-- recommender.py             规则评分与排序逻辑
|   |-- storage.py                 本地导出与阅读状态持久化
|   |-- __init__.py
|-- frontend/
|   |-- app/
|   |   |-- layout.tsx             Next.js 根布局
|   |   |-- page.tsx               前端主应用
|   |   |-- globals.css            全局样式
|   |-- lib/
|   |   |-- api.ts                 前端 API 调用封装
|   |   |-- types.ts               前端数据类型
|   |-- next.config.mjs            将 /api/* 转发到 FastAPI 8000 端口
|   |-- package.json
|   |-- package-lock.json
|   |-- tsconfig.json
|-- data/
|   |-- cache/                     arXiv 短期缓存
|   |-- exports/                   导出结果
|   |-- state/                     本地阅读状态
```

`.gitignore` 已忽略 `.venv/`、`frontend/node_modules/`、`frontend/.next/`、`__pycache__/`、`data/exports/` 等生成目录。

## 运行流程

1. 用户在前端输入研究兴趣、正向关键词、排除词、分类、时间范围和最大结果数。
2. 前端调用 `POST /api/search`。
3. `api.py` 调用 `ArxivClient.search_recent()` 获取 arXiv 论文元数据。
4. `PaperRecommender.recommend()` 根据规则进行评分、解释和排序。
5. 如果启用 `use_ai_review` 且配置了 `DEEPSEEK_API_KEY`，`DeepSeekPaperJudge` 会复评部分候选论文。
6. 后端返回包含生成时间、检索配置和推荐列表的 payload。
7. 前端展示论文卡片、证据、风险、摘要、阅读动作、详情页和阅读队列。
8. 阅读状态通过 `POST /api/status` 保存。
9. 论文详情页中的标签、关键收获和研究笔记通过 `POST /api/knowledge` 保存到本地知识库。
10. 导出通过 `POST /api/export` 写入本地文件。

## 后端安装

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

也可以使用脚本：

```powershell
.\setup_venv.ps1
```

## 前端安装

在 `frontend/` 目录执行：

```powershell
npm install
```

当前工作区里已经存在 `node_modules`，但新环境仍建议显式安装依赖。

## 启动方式

在项目根目录启动后端：

```powershell
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

另开一个终端启动前端：

```powershell
cd frontend
npm run dev
```

浏览器打开：

```text
http://localhost:3000
```

前端会把 `/api/*` 请求转发到 `http://127.0.0.1:8000/api/*`。直接访问 `http://127.0.0.1:8000/api/*` 不是有效页面；要么打开具体 API 路由，要么使用前端地址 `http://localhost:3000`。

## API 路由

### `GET /api/meta`

返回 arXiv 分类、已有阅读状态、知识库条目、默认 DeepSeek 模型，以及当前是否配置了 AI 复评密钥。

### `POST /api/search`

请求示例：

```json
{
  "language": "en",
  "research_interest": "",
  "positive_keywords": "",
  "negative_keywords": "",
  "categories": ["cs.AI", "cs.CL", "cs.LG", "cs.SE"],
  "days_back": 30,
  "max_results": 80,
  "query": "",
  "use_ai_review": false,
  "llm_max_items": 16
}
```

返回内容包括论文元数据、相关性分数、优先级、摘要、推荐理由、证据、风险、匹配主题、不匹配主题、置信度、论文类型、建议动作和阅读状态。

### `POST /api/status`

更新单篇论文阅读状态：

```json
{
  "paper_id": "https://arxiv.org/abs/xxxx.xxxxx",
  "status": "saved"
}
```

### `POST /api/export`

把当前推荐结果写入 `data/exports/`：

```json
{
  "payload": {},
  "export_format": "markdown"
}
```

支持格式：`markdown`、`json`、`bibtex`。

### `GET /api/knowledge`

返回本地知识库条目和条目数量。

### `POST /api/knowledge`

保存或更新单篇论文的知识库条目：

```json
{
  "paper": {},
  "note": "这篇论文与我的研究方向的关系...",
  "tags": ["RAG", "code repair"],
  "key_takeaways": ["提出了新的评估设置", "摘要中没有足够实验细节"]
}
```

## DeepSeek 配置

DeepSeek 复评是可选能力。可以通过环境变量或 `.env` 配置：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
```

可选：

```powershell
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com/chat/completions"
```

后端只会发送标题、摘要、分类、论文元数据和规则检索信号。提示词明确要求模型不能编造全文、实验、数据集、代码可用性等未提供信息。

## 数据与持久化

- 阅读状态保存到 `data/state/reading_status.json`。
- 知识库条目保存到 `data/state/knowledge_base.json`。
- 导出结果保存到 `data/exports/`。
- arXiv 查询缓存保存到 `data/cache/arxiv/`。
- 前端会把当前会话缓存在浏览器 `localStorage` 中，便于页面刷新后保留结果。

## 已知限制

- arXiv 当前已经支持分页，但仍受 `max_results`、API 排序和查询条件限制，不等价于全量镜像。
- 后端在获取结果后仍会按 `published` 时间做本地过滤。
- 推荐质量依赖标题和摘要质量。
- 当前不解析 PDF 全文、引用、代码链接、数据集、实验表格或会议信息。
- DeepSeek 复评只能作为保守的二次筛选，不能视为事实来源。
- 当前还没有自动化测试。

## 下一步建议

优先级最高的是稳定当前端到端链路：

1. 为 arXiv XML 解析、关键词查询、规则评分、状态更新、知识库保存和导出格式增加后端测试。
2. 为前端增加更细的交互测试和更清晰的错误状态。
3. 在阅读历史、主题追踪和知识库规模扩大后，引入 SQLite 或 PostgreSQL。
4. 在规则基线稳定后，增加 embedding 语义检索、PDF 全文理解和基于论文内容的问答。
5. 将 Alerts 和 Analytics 从占位入口扩展为关键词订阅、阅读进度和主题趋势分析。
