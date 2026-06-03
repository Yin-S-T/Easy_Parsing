# Easy Parsing 架构说明

## 1. 产品定位

Easy Parsing 是一个个人科研论文雷达。当前目标不是替代研究者阅读论文，而是减少“发现、初筛、排序、保存、导出、判断是否值得读”这些重复劳动。

当前实现聚焦计算机相关方向的近期 arXiv 论文，核心能力包括：

- arXiv 元数据采集。
- 可解释的规则相关性评分。
- 可选 DeepSeek 复评。
- 本地知识库条目，包括标签、关键收获和研究笔记。
- Next.js 论文筛选与阅读状态仪表盘。
- 本地文件保存阅读状态和导出结果。

## 2. 当前系统形态

```text
Browser
  |
  | Next.js UI: http://localhost:3000
  v
Frontend Application
  |
  | /api/* rewrite
  v
FastAPI Backend: http://127.0.0.1:8000
  |
  |-- arXiv Atom API
  |-- Rule-based recommender
  |-- Optional DeepSeek review
  |-- Local cache / knowledge base / export storage
```

前端负责用户交互和展示；后端负责数据抓取、排序、AI 复评、阅读状态持久化和导出。

## 3. 后端模块

### 3.1 `api.py`

`api.py` 是 FastAPI 应用入口，定义所有对外 API。

当前路由：

- `GET /api/meta`
- `POST /api/search`
- `POST /api/status`
- `POST /api/export`
- `GET /api/knowledge`
- `POST /api/knowledge`

职责：

- 加载 `.env`。
- 配置 CORS。
- 使用 Pydantic 校验请求体。
- 调度 arXiv 客户端、规则推荐器、DeepSeek 复评层和存储函数。
- 把内部 dataclass 结果转换为 API payload。

### 3.2 `src/arxiv_client.py`

`ArxivClient` 访问：

```text
https://export.arxiv.org/api/query
```

当前查询逻辑：

- 构造分类查询，例如 `cat:cs.AI OR cat:cs.CL`。
- 可选加入最多 8 个查询词，格式为 `all:"term"`。
- 按页请求 arXiv 结果。
- 按 `submittedDate` 降序排序。
- 用 `max_results` 限制返回数量。
- 收到结果后按 `days_back` 在本地过滤。
- 使用 `data/cache/arxiv/` 做短期缓存。
- 对重复 paper ID 去重。

解析字段：

- arXiv 页面 URL / ID
- 标题
- 摘要
- 作者
- 发布时间
- 更新时间
- 分类列表
- 主分类
- PDF 链接

失败时会抛出 `ArxivClientError`，由 API 层转换为 503 错误。

### 3.3 `src/models.py`

核心数据模型：

- `Paper`：标准化后的论文元数据。
- `ScoreBreakdown`：可解释的评分信号。
- `Recommendation`：论文、评分结果、推荐理由、证据、风险、AI 复评字段和阅读状态。

这些 dataclass 通过 `to_dict()` 转换后进入 API 响应或导出文件。

### 3.4 `src/recommender.py`

`PaperRecommender` 是当前推荐系统的规则基线。

输入：

- 论文列表
- 用户研究兴趣
- 正向关键词
- 排除关键词
- 选择的 arXiv 分类
- 已有阅读状态
- 输出语言

主要评分因素：

- 标题命中
- 摘要命中
- 从研究兴趣中抽取出的兴趣词命中
- 方法类信号命中，例如 RAG、agent、reasoning、code generation 等
- arXiv 分类匹配
- 新鲜度加分
- 用户排除词惩罚
- survey、review、benchmark 等论文类型风险
- 摘要证据强度

输出：

- `relevance_score`：0 到 100
- `priority`：`high`、`medium`、`low`
- 匹配关键词和主题
- 不匹配主题
- 摘要
- 推荐理由
- 证据片段
- 风险提示
- 置信度
- 论文类型
- 建议动作

这个规则层应该继续作为可解释 fallback。即使后续加入 embedding 或 LLM judge，也不建议直接删除规则基线。

### 3.5 `src/deepseek_client.py`

`DeepSeekPaperJudge` 是可选的二次复评层。

运行条件：

- 请求中 `use_ai_review=true`
- 环境变量中存在 `DEEPSEEK_API_KEY`

候选选择策略：

- 选择排名靠前的高分论文。
- 选择分数中等、不确定性较高的论文。
- 选择低分但仍有关键词命中的探索性论文。
- 总数由 `llm_max_items` 控制。

发送给模型的信息：

- 用户研究画像
- 正向关键词和排除关键词
- 论文标题、摘要、分类和元数据
- 规则分数、匹配主题、不匹配主题

提示词要求模型返回严格 JSON，并禁止编造标题、摘要、分类之外的事实。API 调用失败或 JSON 解析失败时，系统保留规则结果，并在风险字段记录失败原因。

### 3.6 `src/storage.py`

存储层负责：

- `load_reading_statuses()`
- `update_reading_status()`
- `save_recommendations()`
- `load_knowledge_base()`
- `upsert_knowledge_entry()`

文件位置：

```text
data/state/reading_status.json
data/state/knowledge_base.json
data/cache/arxiv/
data/exports/recommendations_YYYYMMDD_HHMMSS.md
data/exports/recommendations_YYYYMMDD_HHMMSS.json
data/exports/recommendations_YYYYMMDD_HHMMSS.bib
```

合法阅读状态：

```text
unread
saved
read_later
read
ignored
```

### 3.7 `src/i18n.py`

当前职责：

- arXiv 分类标签。
- 部分中英文文案。
- `split_keywords()` 工具函数。

需要注意：当前前端的大部分实际页面文案已经放在 `frontend/app/page.tsx` 中，因此 `src/i18n.py` 同时包含后端辅助信息和部分历史遗留文案。后续可以整理为更清晰的共享配置或前端本地化文件。

## 4. 前端模块

### 4.1 `frontend/app/page.tsx`

这是当前前端主应用，是一个客户端 React 页面。

主要区域：

- 侧边栏研究画像表单。
- 导航：Research Radar、Discover、Alerts、Library、Notes、Analytics。
- 指标卡片。
- 论文列表卡片。
- 阅读队列。
- 新兴主题统计。
- 论文详情页。
- 知识库笔记编辑器。
- 搜索、优先级筛选、阅读状态筛选。
- arXiv 分类多选。
- 导出和清空会话操作。

当前真正可用的视图：

- `radar`：重点展示高优先级或高分论文。
- `discover`：展示尚未处理的候选论文。
- `library`：展示已保存、稍后读、已读论文。
- `notes`：展示本地知识库条目。
- `detail`：单篇论文详情分析，并可保存知识库笔记。

当前预留视图：

- `alerts`
- `analytics`

### 4.2 `frontend/lib/api.ts`

前端 API 封装：

- `searchPapers()`
- `getMeta()`
- `updatePaperStatus()`
- `saveKnowledgeEntry()`
- `exportPayload()`

它使用相对路径 `/api/*`，由 Next.js rewrite 转发到 FastAPI。

### 4.3 `frontend/lib/types.ts`

定义前端使用的数据类型：

- `Paper`
- `Recommendation`
- `SearchPayload`
- `SearchRequest`

这些类型和后端返回结构基本对应。

### 4.4 `frontend/next.config.mjs`

配置 API 转发：

```text
/api/:path* -> http://127.0.0.1:8000/api/:path*
```

这样前端可以以同源方式请求 `/api/search`，实际工作交给 FastAPI。

## 5. 主数据流

检索与推荐：

```text
用户研究画像与筛选条件
  |
  v
POST /api/search
  |
  v
ArxivClient.search_recent()
  |
  v
list[Paper]
  |
  v
PaperRecommender.recommend()
  |
  v
list[Recommendation]
  |
  | optional
  v
DeepSeekPaperJudge.refine_recommendations()
  |
  v
SearchPayload
  |
  v
Next.js dashboard
```

阅读状态：

```text
论文卡片操作
  |
  v
POST /api/status
  |
  v
data/state/reading_status.json
```

导出：

```text
当前 SearchPayload
  |
  v
POST /api/export
  |
  v
data/exports/
```

知识库沉淀：

```text
论文详情页
  |
  | 标签 / 关键收获 / 研究笔记
  v
POST /api/knowledge
  |
  v
data/state/knowledge_base.json
  |
  v
Notes / Knowledge Base 视图
```

## 6. 当前优势

- 已经具备端到端 Web 流程。
- 规则推荐器可解释，不依赖 LLM 也能工作。
- DeepSeek 复评是可选能力，并通过 `llm_max_items` 控制成本和延迟。
- 阅读状态持久化已经实现。
- 知识库笔记持久化已经实现。
- arXiv 分页、缓存和去重已经实现。
- 导出格式贴近科研工作流。
- 前端已经有产品骨架，后续可以在现有视图上继续扩展。

## 7. 当前薄弱点

- 没有自动化测试。
- arXiv 仍不是全量镜像，覆盖率受 `max_results`、排序和查询条件限制。
- 知识库仍是本地 JSON，规模变大后需要数据库。
- 前端文案和 `src/i18n.py` 文案存在重复与历史遗留。
- 没有 embedding 语义检索。
- “Code”、“Ask about this paper”、Alerts、Analytics 仍是占位功能。
- `http://127.0.0.1:8000/api/*` 不是可用应用页面，实际入口应是 `http://localhost:3000`。

## 8. 优化路线建议

### 阶段 1：稳定当前基线

优先做：

- 为 arXiv XML 解析、关键词查询构造、评分逻辑、状态更新、知识库保存和导出格式增加后端单元测试。
- 为前端加入 TypeScript 检查和构建检查。
- 对 `days_back`、`max_results`、`llm_max_items`、分类值和阅读状态增加更严格的后端校验。
- 优化 arXiv 不可用、后端离线、DeepSeek 失败、导出失败时的错误提示。

原因：项目已经跑通端到端流程，但后续改推荐逻辑和 UI 时需要测试托底。

### 阶段 2：提高检索覆盖率

建议做：

- 进一步优化 arXiv 请求限速，避免对 arXiv API 造成压力。
- 对缓存增加显式清理策略。
- 做更强的论文 ID 规范化，避免同一论文不同版本或链接形式影响状态保存。
- 增加跨来源去重，为 Semantic Scholar、OpenReview 等来源预留统一 ID 策略。

原因：当前只读取第一页结果，容易漏掉相关论文。

### 阶段 3：提高推荐质量

建议做：

- 把规则评分权重做成可配置项。
- 将“论文类型识别”和“风险惩罚”拆开，避免 benchmark 等词在不同语境下被过度惩罚。
- 改进短语匹配、同义词扩展和领域词表。
- 利用 saved、ignored、read、read_later 形成轻量用户反馈信号。
- 在规则基线稳定后，再加入 embedding 相似度作为附加排序特征。

原因：embedding 很有用，但没有稳定基线和反馈信号时，难以判断改进是否真实有效。

### 阶段 4：沉淀研究记忆

当用户开始长期使用后，可以引入：

- SQLite 或 PostgreSQL。
- 论文元数据表。
- 检索历史表。
- 阅读动作表。
- 用户画像表。
- 主题统计表。
- 周报或月报生成。

如果仍是个人本地工具，SQLite 就足够；如果后续要多人协作或部署，再考虑 PostgreSQL。

### 阶段 5：从论文筛选走向论文理解

在元数据筛选稳定后，再扩展：

- PDF 下载与解析。
- 分章节切分。
- 引用、表格、数据集、指标、限制的结构化抽取。
- 基于 PDF chunk 的“询问这篇论文”。
- 自动生成阅读笔记。
- 自动生成 related work 初稿。
- 检测代码仓库和数据集链接。

这一步是从“是否值得读”走向“帮助读懂论文”的关键。

## 9. 工程边界建议

后续修改建议继续保持这些边界：

- arXiv 网络请求逻辑放在 `src/arxiv_client.py`。
- 推荐评分逻辑放在 `src/recommender.py`。
- LLM 相关行为放在 `src/deepseek_client.py`。
- 本地持久化放在 `src/storage.py`。
- API 编排放在 `api.py`。
- 前端 API 调用放在 `frontend/lib/api.ts`。

不要在一次改动中同时引入数据库、embedding 和 PDF 解析。这三类能力的失败模式不同，应该分阶段落地。
