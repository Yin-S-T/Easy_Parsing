# Easy Parsing：AI 辅助科研文献发现与理解系统增强版规划文档

> 本文档基于 `ARCHITECTURE.md` 的初步规划进一步扩展，目标是把 Easy Parsing 从一个“arXiv 论文筛选工具”逐步发展为面向个人研究者或课题组的科研文献发现、筛选、组织、理解与知识管理助手。

---

## 1. 项目重新定位

### 1.1 一句话定位

**Easy Parsing 是一个面向科研人员的个人 AI 论文侦察员，帮助用户从不断增长的论文流中快速发现、判断、保存和理解真正值得阅读的论文。**

它不是要替代研究者阅读论文，也不是要一开始就做成通用学术搜索引擎，而是优先解决以下核心问题：

- 今天有哪些论文可能和我的研究方向相关？
- 哪几篇最值得我优先阅读？
- 系统为什么推荐这些论文？
- 我是否已经读过、保存过或忽略过这些论文？
- 长期来看，我关注的方向正在发生什么变化？

### 1.2 与现有工具的差异

| 工具类型 | 典型代表 | 优点 | 局限 | Easy Parsing 的切入点 |
|---|---|---|---|---|
| 学术搜索引擎 | Google Scholar, Semantic Scholar | 覆盖广、引用信息强 | 个性化不足，日常筛选成本高 | 聚焦个人研究兴趣的每日筛选 |
| 文献管理工具 | Zotero, Mendeley | 管理引用、PDF、笔记 | 不擅长主动发现和推荐 | 作为前置论文发现与初筛工具 |
| AI 问答工具 | ChatGPT, Perplexity | 解释能力强 | 缺少稳定的个人文献库和长期反馈 | 结合用户 profile、阅读状态和反馈 |
| arXiv 浏览工具 | arXiv Sanity 等 | 新论文发现方便 | 可解释性和本地工作流整合有限 | 更透明的推荐理由与本地知识沉淀 |

---

## 2. 核心产品原则

### 2.1 少即是多

MVP 不应该追求功能完整，而应该追求一个稳定、清晰、可重复使用的核心闭环：

```text
用户研究兴趣
    ↓
拉取新论文
    ↓
清洗与去重
    ↓
相关性评分
    ↓
推荐理由生成
    ↓
用户反馈
    ↓
下一次推荐更准确
```

### 2.2 推荐必须可解释

科研用户不会轻易相信一个黑盒推荐结果。每篇论文至少应给出：

- 命中的正向关键词；
- 命中的负向关键词；
- 匹配到的 arXiv 分类；
- 标题和摘要中支持推荐的证据；
- 推荐分数的主要来源；
- 是否存在风险，例如“看起来相关但可能只是 benchmark/survey”。

### 2.3 AI 结论必须保留依据

所有 AI 摘要、推荐理由、贡献点、局限判断，都应尽量保留原文依据：

```text
AI 结论：
这篇论文关注 repository-level code generation。

依据：
摘要中出现 "repository-level", "code generation", "software engineering agents" 等表达。
```

这样可以降低幻觉风险，也方便用户快速验证。

### 2.4 先服务个人，再扩展课题组

第一阶段建议优先服务个人研究者，而不是马上做多用户协作。个人场景更简单：

- 不需要复杂权限；
- 不需要团队空间；
- 不需要同步冲突处理；
- 更容易验证推荐是否真的有用。

课题组级别的功能可以作为后续扩展，例如共享阅读列表、组会 digest、方向趋势报告等。

---

## 3. 用户场景深化

### 3.1 每日论文侦察

用户每天打开系统，希望快速知道：

- 系统扫描了多少篇论文；
- 哪些论文高相关；
- 哪几篇最值得先读；
- 推荐理由是什么；
- 哪些论文可以暂时忽略。

建议首页明确展示：

```text
今日扫描论文：126 篇
高相关论文：8 篇
建议优先阅读：5 篇
已保存：3 篇
已忽略：12 篇
```

### 3.2 研究方向长期追踪

用户可能长期关注多个方向，例如：

- LLM for Software Engineering
- Retrieval-Augmented Generation
- AI Agents
- Multimodal Reasoning
- AI Safety
- Program Repair
- Code Generation

系统应支持多个研究 profile，而不是只支持一个自由文本兴趣描述。

### 3.3 快速判断一篇论文是否值得读

对每篇论文，系统应该帮助用户回答：

- 这篇论文解决了什么问题？
- 是否和我的方向相关？
- 它的方法路线是什么？
- 它的贡献看起来是否新颖？
- 是否只是一个 survey、benchmark 或 incremental work？
- 是否值得阅读全文？

### 3.4 文献组织与写作准备

后续可支持：

- 阅读列表；
- BibTeX 导出；
- Markdown 导出；
- Related Work 初稿；
- 论文对比表；
- 研究脉络图；
- 课题组周报/月报。

---

## 4. MVP 范围重新定义

### 4.1 MVP 目标

MVP 的目标不应是“做一个功能很多的论文工具”，而是：

> 每天从 arXiv 中筛出用户最可能关心的 5-10 篇论文，并清楚解释为什么推荐。

### 4.2 MVP 必做功能

| 模块 | 功能 | 优先级 |
|---|---|---|
| 数据源 | arXiv API 拉取论文 | P0 |
| 用户输入 | 研究方向、关键词、排除词、arXiv 分类 | P0 |
| 评分 | 标题摘要相关性评分 | P0 |
| 推荐解释 | 命中词、扣分项、推荐理由 | P0 |
| UI | Streamlit 页面展示 | P0 |
| 阅读状态 | save / ignore / read later / read | P0 |
| 导出 | JSON / Markdown / BibTeX | P1 |
| 中英文 | UI 中英文切换 | P1 |
| 反馈记录 | 用户操作日志 | P1 |
| 趋势 | 简单关键词统计 | P2 |

### 4.3 MVP 暂不做功能

- 用户登录；
- 多人协作；
- 复杂数据库；
- 全文 PDF 解析；
- 生产级部署；
- Google Scholar 直接爬取；
- 复杂 citation graph；
- 大规模向量数据库；
- 自动生成完整 related work。

---

## 5. 推荐系统设计

### 5.1 第一版推荐策略

第一版推荐系统应采用“可解释启发式评分”，不要一开始完全依赖 LLM。

推荐评分可以由以下部分构成：

```text
score =
  3.0 * title_positive_keyword_hits
+ 1.5 * abstract_positive_keyword_hits
+ 2.0 * research_interest_overlap
+ 1.5 * category_match
+ 1.0 * method_keyword_match
+ freshness_bonus
- 4.0 * negative_keyword_hits
- 2.0 * excluded_paper_type_penalty
```

### 5.2 评分因素说明

| 因素 | 说明 |
|---|---|
| title_positive_keyword_hits | 标题中命中正向关键词，权重最高 |
| abstract_positive_keyword_hits | 摘要中命中正向关键词 |
| research_interest_overlap | 用户研究兴趣与论文文本的词汇重合 |
| category_match | arXiv 分类是否属于用户关注范围 |
| method_keyword_match | 是否命中用户偏好的方法路线 |
| freshness_bonus | 越新的论文略微加分 |
| negative_keyword_hits | 命中用户排除词则扣分 |
| excluded_paper_type_penalty | survey、position paper 等类型可按用户偏好扣分 |

### 5.3 推荐分级

```text
score >= 8      → High Priority
4 <= score < 8  → Medium Priority
score < 4       → Low Priority
score <= 0      → Hidden / Ignored Candidate
```

### 5.4 推荐理由模板

每篇推荐论文应生成结构化解释：

```text
推荐等级：High

推荐原因：
1. 标题命中关键词：RAG, code generation
2. 摘要命中关键词：retrieval-augmented generation, software engineering
3. arXiv 分类匹配：cs.SE, cs.CL
4. 未命中排除词
5. 发布时间较新

可能风险：
- 仅基于标题和摘要判断，尚未验证实验质量。
```

### 5.5 负样本机制

科研推荐中，负样本和正样本同样重要。建议支持：

```json
{
  "excluded_topics": ["medical", "finance", "biology"],
  "excluded_paper_types": ["survey", "position paper"],
  "negative_keywords": ["radiology", "clinical", "drug discovery"]
}
```

常见论文类型识别词：

```text
survey, review, benchmark, dataset, position paper, tutorial, empirical study
```

---

## 6. 用户研究 Profile 设计

### 6.1 不推荐只使用一个 research_interest 字段

单一字符串难以表达复杂研究兴趣。建议使用结构化 profile。

### 6.2 推荐 Profile 模型

```json
{
  "profile_id": "llm_for_se",
  "profile_name": "LLM for Software Engineering",
  "description": "关注大模型在软件工程中的应用，尤其是代码生成、程序修复、仓库级理解和智能体。",
  "research_goals": [
    "LLM-based code generation",
    "repository-level program repair",
    "RAG for software engineering",
    "software engineering agents"
  ],
  "positive_keywords": [
    "code generation",
    "program repair",
    "repository-level",
    "software engineering agent",
    "RAG",
    "bug fixing"
  ],
  "negative_keywords": [
    "medical",
    "radiology",
    "biology",
    "finance"
  ],
  "preferred_methods": [
    "retrieval-augmented generation",
    "agent-based workflow",
    "benchmark construction",
    "static analysis"
  ],
  "excluded_paper_types": [
    "position paper"
  ],
  "selected_categories": [
    "cs.SE",
    "cs.CL",
    "cs.AI",
    "cs.LG"
  ],
  "preferred_venues": [],
  "language": "zh"
}
```

### 6.3 多 Profile 支持

后续系统应允许用户建立多个 profile：

```text
Profile A: LLM for Software Engineering
Profile B: RAG
Profile C: AI Safety
Profile D: Multimodal Learning
```

每天可以分别生成 digest，也可以合并生成总览。

---

## 7. 数据模型增强

### 7.1 Paper 模型

```json
{
  "id": "string",
  "arxiv_id": "string",
  "title": "string",
  "abstract": "string",
  "authors": ["string"],
  "published": "date",
  "updated": "date",
  "categories": ["string"],
  "primary_category": "string",
  "url": "string",
  "pdf_url": "string",
  "doi": "string | null",
  "comment": "string | null",
  "journal_ref": "string | null",
  "source": "arxiv",
  "source_ids": {
    "arxiv": "string",
    "semantic_scholar": "string | null",
    "openalex": "string | null"
  },
  "collected_at": "datetime",
  "text_hash": "string"
}
```

### 7.2 Recommendation 模型

```json
{
  "paper_id": "string",
  "profile_id": "string",
  "relevance_score": 0.0,
  "priority": "high | medium | low",
  "matched_positive_keywords": ["string"],
  "matched_negative_keywords": ["string"],
  "matched_categories": ["string"],
  "matched_methods": ["string"],
  "freshness_bonus": 0.0,
  "penalties": [
    {
      "type": "negative_keyword",
      "value": "medical",
      "score_delta": -4.0
    }
  ],
  "recommendation_reason": "string",
  "risk_note": "string",
  "summary": "string",
  "created_at": "datetime"
}
```

### 7.3 PaperUserState 模型

```json
{
  "paper_id": "string",
  "profile_id": "string",
  "status": "new | saved | read_later | reading | read | ignored | not_relevant",
  "user_note": "string",
  "tags": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 7.4 Feedback 模型

```json
{
  "feedback_id": "string",
  "paper_id": "string",
  "profile_id": "string",
  "action": "save | ignore | like | dislike | mark_read | not_relevant",
  "reason": "string | null",
  "timestamp": "datetime",
  "profile_snapshot": {}
}
```

---

## 8. 摘要与论文理解设计

### 8.1 MVP：轻量摘要

在不调用 LLM 的情况下，可以基于标题和摘要生成轻量结构：

```text
一句话概括：
该论文提出了一种用于 XXX 的方法，主要面向 YYY 问题。

可能研究问题：
从摘要中抽取包含 problem, challenge, limitation, address 等词的句子。

可能方法：
从摘要中抽取包含 propose, introduce, framework, method, model 等词的句子。

可能实验：
从摘要中抽取包含 experiment, benchmark, dataset, evaluation, result 等词的句子。
```

### 8.2 可选 LLM 摘要

如果用户配置了 API key，可以生成更完整结构：

```json
{
  "one_sentence_summary": "string",
  "research_problem": "string",
  "method": "string",
  "contributions": ["string"],
  "experiments": ["string"],
  "limitations": ["string"],
  "why_it_matters": "string",
  "should_read_reason": "string",
  "evidence_from_abstract": ["string"]
}
```

### 8.3 学术可信性原则

LLM 生成内容必须遵守：

- 不夸大贡献；
- 不臆测论文中没有的信息；
- 区分“论文声称”和“系统判断”；
- 保留摘要原文证据；
- 对不确定内容明确标注“不确定”。

推荐提示词原则：

```text
You should summarize only based on the title and abstract.
Do not infer experimental results not mentioned in the abstract.
If the limitation is not explicit, say "not clear from abstract".
```

---

## 9. 检索系统设计

### 9.1 MVP：关键词检索

第一版使用关键词匹配即可：

- title contains keyword；
- abstract contains keyword；
- category filter；
- date filter；
- negative keyword exclusion。

### 9.2 第二阶段：Hybrid Search

后续建议引入混合检索：

```text
hybrid_score =
  alpha * keyword_score
+ beta * embedding_similarity
+ gamma * citation_or_popularity_score
+ delta * user_feedback_score
```

其中：

- keyword_score 保证可解释性；
- embedding_similarity 捕捉语义相关；
- citation_or_popularity_score 可衡量影响力；
- user_feedback_score 引入个性化。

### 9.3 向量检索字段

可以对以下文本建立 embedding：

```text
title
abstract
title + abstract
LLM-generated structured summary
contribution statements
```

建议优先使用：

```text
embedding_text = title + "\n" + abstract
```

### 9.4 向量数据库选择

| 方案 | 优点 | 适合阶段 |
|---|---|---|
| FAISS | 本地轻量、简单 | 个人 MVP 后期 |
| Qdrant | 易用、过滤强、服务化 | 中期 |
| Milvus | 大规模能力强 | 后期 |
| PostgreSQL + pgvector | 与关系数据整合方便 | 中期到后期 |

个人项目建议优先考虑：

```text
SQLite / JSON → PostgreSQL + pgvector 或 Qdrant
```

---

## 10. 多源聚合设计

### 10.1 数据源扩展优先级

建议顺序：

1. arXiv
2. Semantic Scholar
3. OpenAlex
4. dblp
5. OpenReview
6. Papers with Code
7. conference websites

### 10.2 多源融合挑战

| 问题 | 说明 |
|---|---|
| 去重 | 同一论文可能存在 arXiv、会议版本、Semantic Scholar 条目 |
| 作者名归一 | 作者缩写、同名、顺序变化 |
| 标题变化 | arXiv 版本和会议版本标题可能略有不同 |
| 时间变化 | preprint 时间、会议录用时间、发表时间不同 |
| venue 缺失 | arXiv 初版通常没有 venue |
| API 限制 | 不同平台 rate limit 不同 |

### 10.3 去重策略

第一版可使用：

```text
normalized_title = lowercase(remove_punctuation(title))
title_hash = hash(normalized_title)
```

后续增强：

```text
duplicate_score =
  0.6 * title_similarity
+ 0.2 * author_overlap
+ 0.1 * year_match
+ 0.1 * doi_match
```

如果 `duplicate_score > 0.85`，认为是同一论文。

---

## 11. 评价指标设计

### 11.1 为什么需要 Evaluation

没有评估机制，推荐系统很难迭代。用户觉得“不准”时，开发者也无法知道是关键词、分类、负样本还是排序出了问题。

### 11.2 MVP 指标

| 指标 | 含义 |
|---|---|
| Precision@5 | Top 5 中用户认为相关的比例 |
| Save Rate | 被保存论文 / 推荐论文 |
| Ignore Rate | 被忽略论文 / 推荐论文 |
| Not Relevant Rate | 被标记不相关论文 / 推荐论文 |
| Daily Usefulness Rating | 用户对每日推荐的 1-5 分评分 |
| Repeat Exposure Rate | 已忽略论文再次出现的比例 |

### 11.3 本地评估日志

```json
{
  "date": "2026-04-28",
  "profile_id": "llm_for_se",
  "total_scanned": 126,
  "high_priority_count": 8,
  "medium_priority_count": 21,
  "saved_count": 3,
  "ignored_count": 12,
  "not_relevant_count": 4,
  "top5_precision": 0.6,
  "daily_rating": 4
}
```

### 11.4 人工评估建议

每周抽样检查：

- Top 10 推荐是否真的相关；
- 是否漏掉重要论文；
- 哪些负样本反复误入；
- 推荐理由是否清楚；
- 摘要是否过度推断。

---

## 12. 用户界面设计建议

### 12.1 首页结构

```text
Sidebar
|-- Profile Selector
|-- Language
|-- Research Interest
|-- Positive Keywords
|-- Negative Keywords
|-- arXiv Categories
|-- Time Range
|-- Max Results
|-- Run Search

Main Page
|-- Daily Summary
|-- Metrics Cards
|-- Top Picks
|-- High Priority Papers
|-- Medium Priority Papers
|-- Low Priority / Collapsed
|-- Export Area
```

### 12.2 Paper Card 设计

每篇论文卡片建议包括：

```text
Title
Authors
Published / Updated
Categories
Relevance Score
Priority Badge

One-sentence Summary

Why Recommended:
- matched keywords
- matched categories
- method match
- freshness

Risk Note:
- possible survey
- only abstract-level judgment
- matched negative terms

Actions:
[Save] [Ignore] [Read Later] [Open arXiv] [Open PDF] [Export BibTeX]
```

### 12.3 注意力设计

默认只展开高优先级论文。中低优先级可以折叠。

目标是让用户快速完成判断：

```text
30 秒知道今天该看什么
3 分钟完成保存和忽略
10 分钟读完摘要和推荐理由
```

---

## 13. 导出与工作流集成

### 13.1 MVP 导出格式

建议支持：

- JSON
- Markdown
- BibTeX
- CSV

### 13.2 Markdown Digest 模板

```markdown
# Daily Paper Digest - 2026-04-28

## Summary

- Scanned papers: 126
- High priority: 8
- Saved: 3

## Top Picks

### 1. Paper Title

- Authors:
- arXiv:
- PDF:
- Categories:
- Score:
- Why recommended:
- Summary:
- Notes:

## Medium Priority

...
```

### 13.3 BibTeX 导出

即使第一版只有 arXiv 信息，也可以生成基本 BibTeX：

```bibtex
@misc{arxiv_id,
  title={Paper Title},
  author={Author A and Author B},
  year={2026},
  eprint={arXiv ID},
  archivePrefix={arXiv},
  primaryClass={cs.SE}
}
```

### 13.4 后续集成

优先级建议：

1. Markdown for Obsidian / Notion
2. BibTeX for LaTeX
3. Zotero import
4. Notion API
5. Readwise / Logseq / 飞书文档

---

## 14. 技术架构建议

### 14.1 MVP 技术栈

```text
Language: Python
UI: Streamlit
Data Source: arXiv API
Storage: Local JSON / SQLite
Scoring: Heuristic scoring
Summary: Rule-based summary + optional LLM
Export: JSON / Markdown / BibTeX
```

### 14.2 建议文件结构

```text
Easy Parsing/
|-- README.md
|-- ARCHITECTURE.md
|-- requirements.txt
|-- app.py
|-- config/
|   |-- default_profiles.json
|-- data/
|   |-- papers/
|   |-- recommendations/
|   |-- feedback/
|   |-- exports/
|-- src/
|   |-- collectors/
|   |   |-- arxiv_collector.py
|   |
|   |-- models/
|   |   |-- paper.py
|   |   |-- profile.py
|   |   |-- recommendation.py
|   |   |-- feedback.py
|   |
|   |-- ranking/
|   |   |-- keyword_scorer.py
|   |   |-- explanation_builder.py
|   |
|   |-- summarization/
|   |   |-- rule_based_summary.py
|   |   |-- llm_summary.py
|   |
|   |-- storage/
|   |   |-- json_store.py
|   |   |-- sqlite_store.py
|   |
|   |-- export/
|   |   |-- markdown_exporter.py
|   |   |-- bibtex_exporter.py
|   |
|   |-- ui/
|   |   |-- components.py
|   |   |-- pages.py
|   |
|   |-- utils/
|       |-- text_cleaning.py
|       |-- date_utils.py
```

### 14.3 为什么建议引入 SQLite

虽然 JSON 简单，但 SQLite 会更适合稍微长期使用：

| JSON | SQLite |
|---|---|
| 简单直接 | 查询方便 |
| 适合导出 | 适合状态管理 |
| 不适合复杂过滤 | 支持索引 |
| 文件容易膨胀 | 更适合长期本地库 |

建议路线：

```text
最初 JSON → 很快引入 SQLite → 后续 PostgreSQL
```

---

## 15. 学术能力增强方向

### 15.1 论文贡献识别

后续可以让系统识别论文贡献类型：

```text
- New method
- New benchmark
- New dataset
- Empirical study
- Theoretical analysis
- System implementation
- Survey
- Negative result
```

这对研究者非常有用，因为不同用户对论文类型的偏好不同。

### 15.2 方法路线抽取

可以抽取：

```text
Problem
Method
Architecture
Data
Evaluation
Baseline
Metric
Claimed Contribution
Limitation
```

形成结构化卡片。

### 15.3 论文对比

对多篇论文生成对比表：

| Paper | Problem | Method | Dataset | Metric | Contribution | Limitation |
|---|---|---|---|---|---|---|

这对写 related work 很有价值。

### 15.4 研究脉络生成

对某一方向生成：

```text
早期方法
    ↓
关键突破
    ↓
代表论文
    ↓
当前热点
    ↓
未解决问题
```

但这一功能应放在知识库和多源数据成熟之后。

---

## 16. RAG 与论文问答规划

### 16.1 不建议 MVP 做全文 RAG

全文 PDF 解析会带来很多复杂问题：

- PDF 结构混乱；
- 公式和表格难解析；
- 参考文献干扰；
- 图表理解困难；
- chunk 切分策略复杂；
- hallucination 风险更高。

### 16.2 推荐发展路径

```text
Phase A: title + abstract search
Phase B: structured summary search
Phase C: introduction + conclusion parsing
Phase D: full PDF parsing
Phase E: paper-level QA
Phase F: multi-paper QA
```

### 16.3 RAG 的基本数据结构

```json
{
  "chunk_id": "string",
  "paper_id": "string",
  "section": "introduction | method | experiment | conclusion",
  "text": "string",
  "page": 3,
  "embedding_id": "string"
}
```

### 16.4 QA 回答原则

论文问答必须引用来源：

```text
回答：
该论文主要提出了 XXX。

依据：
- Abstract: ...
- Introduction: ...
- Method Section: ...
```

不要只生成无依据的自然语言回答。

---

## 17. 风险与限制

### 17.1 推荐误判

仅基于标题和摘要，可能误判论文真实贡献和质量。

缓解方式：

- 明确标注“abstract-level judgment”；
- 引入用户反馈；
- 后续加入 introduction/conclusion；
- 保留推荐依据。

### 17.2 关键词偏差

关键词系统容易漏掉语义相关但措辞不同的论文。

缓解方式：

- 后续引入 embedding；
- 支持同义词扩展；
- 支持用户保存正样本后自动扩展关键词。

### 17.3 AI 摘要幻觉

LLM 可能生成摘要中不存在的内容。

缓解方式：

- 限制模型只能根据标题摘要总结；
- 要求输出 evidence；
- 对不确定内容输出 unknown；
- 后续引入原文 citation。

### 17.4 多源数据质量问题

不同学术平台数据不一致。

缓解方式：

- 保留 source_ids；
- 标注数据来源；
- 不覆盖原始字段；
- 做字段级 confidence。

### 17.5 用户隐私

研究兴趣和阅读记录可能具有隐私性。

缓解方式：

- MVP 默认本地存储；
- API key 用户自管；
- 后续若上线云端，需要明确隐私策略。

---

## 18. 分阶段路线图

### Phase 1: arXiv Daily Scout

目标：完成个人每日论文筛选闭环。

功能：

- arXiv 拉取；
- profile 输入；
- 关键词评分；
- 推荐理由；
- Streamlit UI；
- 保存、忽略、稍后读；
- JSON / Markdown 导出。

### Phase 2: Feedback and Reading Workflow

目标：让系统从一次性搜索工具变成个人阅读工作流。

功能：

- 阅读状态管理；
- 用户反馈日志；
- 简单评估指标；
- BibTeX 导出；
- 多 profile；
- 每日 digest 历史记录。

### Phase 3: AI Understanding

目标：提高论文理解效率。

功能：

- LLM 结构化摘要；
- 贡献点提取；
- 方法和实验提取；
- 局限识别；
- 论文类型识别；
- 中英文解释。

### Phase 4: Multi-source Metadata Enrichment

目标：增强数据覆盖和元信息质量。

功能：

- Semantic Scholar；
- OpenAlex；
- dblp；
- OpenReview；
- 去重；
- venue 信息；
- citation 信息；
- code link。

### Phase 5: Vector Search and Knowledge Base

目标：形成个人文献知识库。

功能：

- embedding；
- hybrid search；
- topic clustering；
- semantic paper retrieval；
- paper similarity；
- direction-level trend analysis。

### Phase 6: Research Copilot

目标：支持研究写作与方向分析。

功能：

- related work 初稿；
- multi-paper comparison；
- research timeline；
- reading roadmap；
- weekly/monthly report；
- Zotero / Obsidian / Notion integration；
- 课题组共享 digest。

---

## 19. 建议的近期开发任务清单

### Week 1: 数据和基础 UI

- [ ] 实现 arXiv API 拉取；
- [ ] 定义 Paper / Profile / Recommendation 数据模型；
- [ ] 实现 Streamlit sidebar；
- [ ] 展示论文列表；
- [ ] 支持按时间和分类筛选。

### Week 2: 推荐评分

- [ ] 实现关键词评分；
- [ ] 实现负向关键词扣分；
- [ ] 实现 priority 分级；
- [ ] 实现推荐理由生成；
- [ ] 显示 score breakdown。

### Week 3: 阅读状态和导出

- [ ] 支持 save / ignore / read later；
- [ ] 保存用户反馈；
- [ ] 支持 JSON 导出；
- [ ] 支持 Markdown digest；
- [ ] 支持基础 BibTeX 导出。

### Week 4: 可用性优化

- [ ] 优化论文卡片；
- [ ] 增加 Top Picks；
- [ ] 增加每日统计；
- [ ] 增加 profile 保存；
- [ ] 增加简单评估指标。

---

## 20. 成功标准

MVP 是否成功，不应只看功能是否完成，而应看它是否真的减少了科研筛选负担。

建议使用以下标准：

```text
用户每天是否愿意打开？
Top 5 推荐中是否至少有 2-3 篇值得看？
用户是否愿意保存推荐结果？
用户是否觉得推荐理由可信？
系统是否减少了手动刷 arXiv 的时间？
一周后用户是否还想继续用？
```

如果这些问题的答案是肯定的，说明 MVP 方向正确。

---

## 21. 总结

Easy Parsing 最有潜力的方向不是做一个“大而全”的论文搜索平台，而是做一个**懂用户研究方向、能解释推荐理由、能长期积累反馈的个人科研文献助手**。

第一阶段最重要的不是模型复杂度，而是以下五点：

1. 推荐结果足够相关；
2. 推荐理由足够透明；
3. 用户操作足够简单；
4. 阅读状态能够沉淀；
5. 反馈可以用于下一轮改进。

当这个闭环跑通后，再逐步加入 LLM 摘要、多源数据、向量检索、知识库问答和 related work 辅助，项目就会从一个轻量 arXiv 工具自然成长为真正的 Research Copilot。
