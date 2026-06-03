'use client';

import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, BarChart3, Bell, Bookmark, BookOpenText, Brain, Database, FileText, HelpCircle, Library, Lightbulb, LineChart, NotebookPen, Search, Send, Sparkles, Star, Target, XCircle } from 'lucide-react';
import { exportPayload, getMeta, saveKnowledgeEntry, searchPapers, updatePaperStatus } from '../lib/api';
import { KnowledgeEntry, Recommendation, SearchPayload, SearchRequest } from '../lib/types';

type Lang = 'en' | 'zh';
type View = 'radar' | 'discover' | 'alerts' | 'library' | 'notes' | 'analytics';

const defaultCategories = ['cs.AI', 'cs.CL', 'cs.LG', 'cs.SE'];
const fallbackCategories: Record<string, string> = {
  'Artificial Intelligence': 'cs.AI',
  'Computation and Language': 'cs.CL',
  'Machine Learning': 'cs.LG',
  'Computer Vision': 'cs.CV',
  'Software Engineering': 'cs.SE',
  'Information Retrieval': 'cs.IR',
  'Cryptography and Security': 'cs.CR',
  'Human-Computer Interaction': 'cs.HC',
};
const initialPayload: SearchPayload = { generated_at: '', config: {}, recommendations: [] };
const initialRequest: SearchRequest = {
  language: 'en',
  research_interest: '',
  positive_keywords: '',
  negative_keywords: '',
  categories: defaultCategories,
  days_back: 30,
  max_results: 80,
  query: '',
  use_ai_review: false,
  llm_max_items: 16,
};

const copy = {
  en: {
    nav: ['Research Radar', 'Discover', 'Alerts', 'Library', 'Notes', 'Analytics'],
    profile: 'Research Profile',
    interests: 'Research Interests',
    keywords: 'Positive Keywords',
    exclusions: 'Exclusions',
    categories: 'arXiv Categories',
    recency: 'Recency',
    maxResults: 'Max Results',
    aiReview: 'AI Review',
    run: 'Run Search',
    scanning: 'Scanning...',
    title: "Today's Research Radar",
    updated: 'Updated',
    search: 'Search papers, authors, keywords, notes...',
    scanned: 'Scanned',
    relevant: 'Relevant',
    high: 'High Priority',
    saved: 'Saved',
    top: 'Priority Papers',
    export: 'Export Digest',
    queue: 'Reading Queue',
    trends: 'Emerging Topics',
    quick: 'Open Detail',
    pdf: 'PDF',
    code: 'Code',
    relevance: 'Relevance',
    evidence: 'Evidence',
    emptyTitle: 'Nothing here yet',
    emptyBody: 'Run a search or save papers into the knowledge base.',
    paperAnalysis: 'Paper Analysis',
    overview: 'AI Overview',
    ask: 'Ask about this paper',
    askPlaceholder: 'PDF-grounded Q&A is not connected yet.',
    risks: 'Risks',
    evidenceSnippets: 'Evidence Snippets',
    save: 'Save',
    read: 'Read',
    ignore: 'Ignore',
    readLater: 'Read later',
    language: 'Language',
    exported: 'Export task completed',
    unavailable: 'This action is reserved for a later capability.',
    all: 'All',
    status: 'Status',
    priority: 'Priority',
    modelHint: 'Uses the backend private key when enabled. No key is stored in the browser.',
    clearSession: 'Clear session',
    sessionCleared: 'Current session cleared.',
    abstractPreview: 'Original Abstract',
    showFull: 'Show full abstract',
    hideFull: 'Hide full abstract',
    confidence: 'Confidence',
    paperType: 'Paper Type',
    recommendedAction: 'Action',
    knowledge: 'Knowledge Base',
    knowledgeNote: 'Research Note',
    tags: 'Tags',
    takeaways: 'Key Takeaways',
    saveKnowledge: 'Save to Knowledge Base',
    savingKnowledge: 'Saving...',
    savedKnowledge: 'Knowledge entry saved.',
    notePlaceholder: 'Write what this paper contributes, why it matters, and how it connects to your work.',
    tagsPlaceholder: 'RAG, code repair, evaluation',
    takeawaysPlaceholder: 'One takeaway per line',
    noKnowledge: 'No knowledge entries yet. Open a paper detail page and save your notes.',
    categoryPreset: 'Core CS',
    selectNone: 'Clear',
    llmItems: 'AI Review Limit',
  },
  zh: {
    nav: ['研究雷达', '发现', '提醒', '文库', '笔记', '分析'],
    profile: '研究画像',
    interests: '研究兴趣',
    keywords: '正向关键词',
    exclusions: '排除词',
    categories: 'arXiv 分类',
    recency: '时间范围',
    maxResults: '最大数量',
    aiReview: 'AI 复评',
    run: '开始检索',
    scanning: '检索中...',
    title: '今日研究雷达',
    updated: '已更新',
    search: '搜索论文、作者、关键词、笔记...',
    scanned: '扫描论文',
    relevant: '相关论文',
    high: '重点阅读',
    saved: '已保存',
    top: '优先推荐论文',
    export: '导出摘要',
    queue: '阅读队列',
    trends: '新兴主题',
    quick: '打开详情',
    pdf: 'PDF',
    code: '代码',
    relevance: '相关性',
    evidence: '关键依据',
    emptyTitle: '这里暂时为空',
    emptyBody: '先运行检索，或在论文详情页把论文保存到知识库。',
    paperAnalysis: '论文分析',
    overview: 'AI 概览',
    ask: '询问这篇论文',
    askPlaceholder: '基于 PDF 的问答能力尚未接入。',
    risks: '风险',
    evidenceSnippets: '证据片段',
    save: '保存',
    read: '已读',
    ignore: '忽略',
    readLater: '稍后读',
    language: '语言',
    exported: '导出任务已完成',
    unavailable: '该动作是后续能力预留入口。',
    all: '全部',
    status: '状态',
    priority: '优先级',
    modelHint: '开启后使用后端私有密钥，浏览器不保存任何密钥。',
    clearSession: '清空会话',
    sessionCleared: '当前会话已清空。',
    abstractPreview: '原始摘要',
    showFull: '展开完整摘要',
    hideFull: '收起完整摘要',
    confidence: '置信度',
    paperType: '论文类型',
    recommendedAction: '建议动作',
    knowledge: '知识库',
    knowledgeNote: '研究笔记',
    tags: '标签',
    takeaways: '关键收获',
    saveKnowledge: '保存到知识库',
    savingKnowledge: '保存中...',
    savedKnowledge: '知识条目已保存。',
    notePlaceholder: '记录这篇论文的贡献、为什么重要，以及它如何连接你的研究。',
    tagsPlaceholder: 'RAG, code repair, evaluation',
    takeawaysPlaceholder: '每行一个关键收获',
    noKnowledge: '还没有知识库条目。打开论文详情页并保存笔记即可沉淀。',
    categoryPreset: '核心 CS',
    selectNone: '清空',
    llmItems: 'AI 复评数量',
  },
} as const;

const formatDate = (value?: string) => value ? value.slice(0, 10) : '-';
const formatTime = (value: string) => value ? value.slice(11, 16) : 'not searched yet';
const firstSentences = (text: string, count = 2) => text.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, count).join(' ');
const splitComma = (value: string) => value.split(',').map((item) => item.trim()).filter(Boolean);
const splitLines = (value: string) => value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
const priorityLabel = (priority: Recommendation['priority'], lang: Lang) => lang === 'zh' ? ({ high: '重点', medium: '可选', low: '低优先级' }[priority]) : ({ high: 'High', medium: 'Medium', low: 'Low' }[priority]);
const confidenceLabel = (item: Recommendation) => item.confidence ?? 'medium';
const paperTypeLabel = (item: Recommendation) => item.paper_type ? item.paper_type.replaceAll('_', ' ') : 'unknown';
const readingAction = (item: Recommendation, lang: Lang) => {
  const action = item.recommended_action ?? 'skim';
  const labels = lang === 'zh'
    ? { read_now: '优先阅读', skim: '快速扫读', save_for_later: '稍后保存', ignore: '忽略' }
    : { read_now: 'Read now', skim: 'Skim', save_for_later: 'Save for later', ignore: 'Ignore' };
  return labels[action];
};

function applyStatuses(payload: SearchPayload, statuses: Record<string, string>): SearchPayload {
  return {
    ...payload,
    recommendations: payload.recommendations.map((item) => ({
      ...item,
      reading_status: statuses[item.paper.id] ?? item.reading_status,
    })),
  };
}

function EmptyState({ lang }: { lang: Lang }) {
  const text = copy[lang];
  return <section className="panel"><div className="panel-title"><span>{text.emptyTitle}</span></div><p className="abstract">{text.emptyBody}</p></section>;
}

function Sidebar({ lang, setLang, view, setView, request, setRequest, onSearch, loading, categories }: {
  lang: Lang;
  setLang: (lang: Lang) => void;
  view: View;
  setView: (view: View) => void;
  request: SearchRequest;
  setRequest: (request: SearchRequest) => void;
  onSearch: () => void;
  loading: boolean;
  categories: Record<string, string>;
}) {
  const text = copy[lang];
  const nav = [[text.nav[0], 'radar', Target], [text.nav[1], 'discover', Search], [text.nav[2], 'alerts', Bell], [text.nav[3], 'library', Library], [text.nav[4], 'notes', NotebookPen], [text.nav[5], 'analytics', BarChart3]] as const;
  const categoryEntries = Object.entries(categories);
  const toggleCategory = (code: string) => {
    const next = request.categories.includes(code)
      ? request.categories.filter((item) => item !== code)
      : [...request.categories, code];
    setRequest({ ...request, categories: next.length ? next : [code] });
  };

  return (
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">EP</div><span>Easy Parsing</span></div>
      <div className="nav">
        {nav.map(([name, id, Icon]) => <button className={`nav-item ${view === id ? 'active' : ''}`} key={id} onClick={() => setView(id)}><Icon size={16}/>{name}</button>)}
      </div>
      <div>
        <div className="side-label">{text.profile}</div>
        <div className="field"><label>{text.language}</label><select value={lang} onChange={(event) => { const next = event.target.value as Lang; setLang(next); setRequest({ ...request, language: next }); }}><option value="en">English</option><option value="zh">中文</option></select></div>
        <div className="field"><label>{text.interests}</label><textarea value={request.research_interest} onChange={(event) => setRequest({ ...request, research_interest: event.target.value })}/></div>
        <div className="field"><label>{text.keywords}</label><input value={request.positive_keywords} onChange={(event) => setRequest({ ...request, positive_keywords: event.target.value })}/></div>
        <div className="field"><label>{text.exclusions}</label><input value={request.negative_keywords} onChange={(event) => setRequest({ ...request, negative_keywords: event.target.value })}/></div>
        <div className="field">
          <label>{text.categories}</label>
          <div className="category-actions">
            <button className="link" onClick={() => setRequest({ ...request, categories: defaultCategories })}>{text.categoryPreset}</button>
            <button className="link" onClick={() => setRequest({ ...request, categories: [defaultCategories[0]] })}>{text.selectNone}</button>
          </div>
          <div className="category-grid">
            {categoryEntries.map(([label, code]) => (
              <label className={`category-pill ${request.categories.includes(code) ? 'selected' : ''}`} key={code}>
                <input type="checkbox" checked={request.categories.includes(code)} onChange={() => toggleCategory(code)}/>
                <span>{code}</span>
                <small>{label}</small>
              </label>
            ))}
          </div>
        </div>
        <div className="field"><label>{text.recency}</label><select value={request.days_back} onChange={(event) => setRequest({ ...request, days_back: Number(event.target.value) })}><option value={7}>Last 7 days</option><option value={14}>Last 14 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option><option value={180}>Last 180 days</option></select></div>
        <div className="field"><label>{text.maxResults}</label><input type="number" min={1} max={300} value={request.max_results} onChange={(event) => setRequest({ ...request, max_results: Number(event.target.value) })}/></div>
        <div className="field"><label>{text.aiReview}</label><select value={request.use_ai_review ? 'on' : 'off'} onChange={(event) => setRequest({ ...request, use_ai_review: event.target.value === 'on' })}><option value="off">Off</option><option value="on">On</option></select><small className="meta">{text.modelHint}</small></div>
        <div className="field"><label>{text.llmItems}</label><input type="number" min={0} max={50} value={request.llm_max_items} onChange={(event) => setRequest({ ...request, llm_max_items: Number(event.target.value) })}/></div>
        <button className="action primary" onClick={onSearch} disabled={loading}>{loading ? text.scanning : text.run}</button>
      </div>
    </aside>
  );
}

function MetricCards({ recommendations, knowledgeBase, lang }: { recommendations: Recommendation[]; knowledgeBase: Record<string, KnowledgeEntry>; lang: Lang }) {
  const text = copy[lang];
  const counts = useMemo(() => {
    const high = recommendations.filter((item) => item.priority === 'high').length;
    const medium = recommendations.filter((item) => item.priority === 'medium').length;
    const saved = recommendations.filter((item) => ['saved', 'read_later', 'read'].includes(item.reading_status)).length;
    return { scanned: recommendations.length, relevant: high + medium, high, saved: Math.max(saved, Object.keys(knowledgeBase).length) };
  }, [recommendations, knowledgeBase]);
  const metrics = [[text.scanned, counts.scanned, FileText, 'blue'], [text.relevant, counts.relevant, Target, 'green'], [text.high, counts.high, Star, 'gold'], [text.saved, counts.saved, Database, 'purple']] as const;
  return <div className="metrics">{metrics.map(([label, value, Icon, color]) => <div className="metric-card" key={label}><div className={`metric-icon ${color}`}><Icon size={21}/></div><div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-delta">live</div></div></div>)}</div>;
}

function PaperCard({ item, index, lang, onSelect, onStatus, onUnavailable }: {
  item: Recommendation;
  index: number;
  lang: Lang;
  onSelect: (item: Recommendation) => void;
  onStatus: (paperId: string, status: string) => void;
  onUnavailable: () => void;
}) {
  const text = copy[lang];
  const topics = item.matched_topics.length ? item.matched_topics : item.matched_keywords;
  const risks = item.mismatch_topics.length ? item.mismatch_topics : item.risks;
  const [showAbstract, setShowAbstract] = useState(false);
  const abstractText = item.paper.abstract || '';
  const abstractPreview = firstSentences(abstractText, 2) || abstractText.slice(0, 260);

  return (
    <article className="paper-card">
      <div className="paper-row">
        <div className="rank">{index}</div>
        <div>
          <div className="badges">
            <span className={`badge ${item.priority}`}>{priorityLabel(item.priority, lang)}</span>
            <span className="badge low">{text.confidence}: {confidenceLabel(item)}</span>
            <span className="badge low">{text.paperType}: {paperTypeLabel(item)}</span>
            <span className="badge medium">{text.recommendedAction}: {readingAction(item, lang)}</span>
          </div>
          <div className="paper-title">{item.paper.title}</div>
          <div className="authors">{item.paper.authors.slice(0, 4).join(', ')}{item.paper.authors.length > 4 ? ' et al.' : ''}</div>
          <div className="meta">arXiv: {item.paper.id} · {item.paper.primary_category} · {formatDate(item.paper.published)}</div>
          <p className="abstract">{item.summary || item.paper.abstract}</p>
          <div className="abstract-box">
            <div className="evidence-title">{text.abstractPreview}</div>
            <p className="abstract">{showAbstract ? abstractText : abstractPreview}</p>
            {abstractText.length > abstractPreview.length && <button className="link" onClick={() => setShowAbstract(!showAbstract)}>{showAbstract ? text.hideFull : text.showFull}</button>}
          </div>
          <div className="evidence-grid">
            <div className="actions">
              <button className="action" onClick={() => onSelect(item)}><Sparkles size={14}/>{text.quick}</button>
              <a className="action" href={item.paper.pdf_url} target="_blank"><FileText size={14}/>{text.pdf}</a>
              <a className="action" href={item.paper.url} target="_blank">arXiv</a>
              <button className="action" onClick={onUnavailable}><BookOpenText size={14}/>{text.code}</button>
            </div>
            <div><div className="evidence-title">{text.evidence}</div><ul className="evidence-list">{item.evidence.slice(0, 3).map((entry) => <li key={entry}>{entry}</li>)}</ul></div>
          </div>
          <div className="badges">
            {topics.slice(0, 4).map((topic) => <span className="badge low" key={topic}>{topic}</span>)}
            {risks.slice(0, 2).map((risk) => <span className="badge risk" key={risk}>{risk}</span>)}
          </div>
          <div className="actions">
            <button className="action" onClick={() => onStatus(item.paper.id, 'saved')}>{text.save}</button>
            <button className="action" onClick={() => onStatus(item.paper.id, 'read_later')}>{text.readLater}</button>
            <button className="action" onClick={() => onStatus(item.paper.id, 'read')}>{text.read}</button>
            <button className="action" onClick={() => onStatus(item.paper.id, 'ignored')}><XCircle size={14}/>{text.ignore}</button>
          </div>
        </div>
        <div className="score"><small>{text.relevance}</small><strong>{Math.round(item.relevance_score)}%</strong><div className="scorebar"><span style={{ width: `${Math.max(3, item.relevance_score)}%` }}/></div></div>
      </div>
    </article>
  );
}

function RightRail({ recommendations, knowledgeBase, lang, onViewAll }: { recommendations: Recommendation[]; knowledgeBase: Record<string, KnowledgeEntry>; lang: Lang; onViewAll: () => void }) {
  const text = copy[lang];
  const queue = recommendations.filter((item) => ['saved', 'read_later', 'read'].includes(item.reading_status)).slice(0, 5);
  const topics = Array.from(recommendations.flatMap((item) => item.matched_topics.length ? item.matched_topics : item.matched_keywords).reduce((map, topic) => map.set(topic, (map.get(topic) ?? 0) + 1), new Map<string, number>()).entries()).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const knowledgeEntries = Object.values(knowledgeBase).sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, 4);

  return (
    <aside className="right-rail">
      <section className="panel"><div className="panel-title"><span>{text.queue}</span><button className="link" onClick={onViewAll}>{text.all}</button></div>{queue.map((item, index) => <div className="queue-item" key={item.paper.id}><div className="queue-rank">{index + 1}</div><div><div className="queue-title">{item.paper.title}</div><div className="queue-meta">{item.reading_status} · {item.paper.primary_category}</div></div><Bookmark size={14}/></div>)}{queue.length === 0 && <div className="queue-meta">{text.emptyBody}</div>}</section>
      <section className="panel"><div className="panel-title"><span>{text.knowledge}</span><Brain size={16}/></div>{knowledgeEntries.map((entry) => <div className="queue-item" key={entry.paper.id}><div className="queue-rank"><NotebookPen size={13}/></div><div><div className="queue-title">{entry.paper.title}</div><div className="queue-meta">{entry.tags.slice(0, 3).join(', ') || formatDate(entry.updated_at)}</div></div></div>)}{knowledgeEntries.length === 0 && <div className="queue-meta">{text.noKnowledge}</div>}</section>
      <section className="panel"><div className="panel-title"><span>{text.trends}</span><LineChart size={16}/></div>{topics.map(([topic, count]) => <div className="trend" key={topic}><span>{topic}</span><span className="spark"/><span className="positive">{count}</span></div>)}{topics.length === 0 && <div className="queue-meta">{lang === 'zh' ? '检索后会基于匹配主题统计。' : 'Trends are counted after search.'}</div>}</section>
    </aside>
  );
}

function DetailView({ item, lang, entry, onBack, onStatus, onSaveKnowledge, savingKnowledge, onUnavailable }: {
  item: Recommendation;
  lang: Lang;
  entry?: KnowledgeEntry;
  onBack: () => void;
  onStatus: (paperId: string, status: string) => void;
  onSaveKnowledge: (item: Recommendation, note: string, tags: string[], keyTakeaways: string[]) => Promise<void>;
  savingKnowledge: boolean;
  onUnavailable: () => void;
}) {
  const text = copy[lang];
  const [note, setNote] = useState(entry?.note ?? '');
  const [tags, setTags] = useState((entry?.tags ?? item.matched_topics.slice(0, 4)).join(', '));
  const [takeaways, setTakeaways] = useState((entry?.key_takeaways ?? item.evidence.slice(0, 3)).join('\n'));
  const abstractPreview = firstSentences(item.paper.abstract, 3) || 'Insufficient evidence from title and abstract.';
  const sections = [
    [lang === 'zh' ? '研究问题' : 'Research Question', abstractPreview, HelpCircle],
    [lang === 'zh' ? '核心想法' : 'Core Idea', item.summary || abstractPreview, Lightbulb],
    [lang === 'zh' ? '证据与验证' : 'Evidence & Validation', item.evidence.length ? item.evidence.join(' · ') : 'No concrete evidence is visible from metadata.', LineChart],
    [lang === 'zh' ? '局限与不确定性' : 'Limitations / Uncertainties', item.risks.concat(item.mismatch_topics).join(' · ') || 'Analysis is based only on title, abstract, and metadata.', AlertTriangle],
    [lang === 'zh' ? '为什么值得关注' : 'Why It Matters to You', item.reason || 'Relevance depends on overlap with your research profile.', Target],
  ] as const;

  return (
    <main className="main">
      <div className="topbar"><button className="link" onClick={onBack}>‹ {text.paperAnalysis}</button><div className="top-actions"><Bell size={18} onClick={onUnavailable}/><HelpCircle size={18} onClick={onUnavailable}/><div className="avatar"/></div></div>
      <div className="detail">
        <section>
          <div className="meta">arXiv · {item.paper.primary_category} · {formatDate(item.paper.published)}</div>
          <h1 className="detail-title">{item.paper.title}</h1>
          <div className="actions"><span className="action">arXiv: {item.paper.id}</span><span className="action">{paperTypeLabel(item)}</span><span className="action primary">{readingAction(item, lang)}</span><button className="action" onClick={() => onStatus(item.paper.id, 'saved')}>{text.save}</button></div>
          <div className="detail-card"><strong>{text.overview}</strong><p className="abstract">{item.summary || item.paper.abstract}</p></div>
          {sections.map(([title, body, Icon], index) => <div className="detail-card" key={title}><div className="analysis-row"><div className="analysis-icon"><Icon size={18}/></div><div><h3>{index + 1}. {title}</h3><p>{body}</p></div></div></div>)}
          <div className="detail-card">
            <strong>{text.ask}</strong>
            <div className="command-input"><input placeholder={text.askPlaceholder}/><button className="send" onClick={onUnavailable}><Send size={16}/></button></div>
          </div>
        </section>
        <aside>
          <section className="panel">
            <div className="panel-title"><span>{text.relevance}</span></div>
            <div className="score"><strong>{Math.round(item.relevance_score)}</strong><small>{priorityLabel(item.priority, lang)} · {text.confidence}: {confidenceLabel(item)}</small></div>
          </section>
          <section className="panel knowledge-editor">
            <div className="panel-title"><span>{text.knowledge}</span><Database size={16}/></div>
            <div className="field"><label>{text.tags}</label><input value={tags} onChange={(event) => setTags(event.target.value)} placeholder={text.tagsPlaceholder}/></div>
            <div className="field"><label>{text.takeaways}</label><textarea value={takeaways} onChange={(event) => setTakeaways(event.target.value)} placeholder={text.takeawaysPlaceholder}/></div>
            <div className="field"><label>{text.knowledgeNote}</label><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder={text.notePlaceholder}/></div>
            <button className="action primary" onClick={() => onSaveKnowledge(item, note, splitComma(tags), splitLines(takeaways))} disabled={savingKnowledge}>{savingKnowledge ? text.savingKnowledge : text.saveKnowledge}</button>
          </section>
          <section className="panel"><div className="panel-title"><span>{text.evidenceSnippets}</span></div>{item.evidence.slice(0, 4).map((entryText) => <div className="quote" key={entryText}>“{entryText}”</div>)}</section>
          <section className="panel"><div className="panel-title"><span>{text.risks}</span></div>{item.risks.concat(item.mismatch_topics).slice(0, 4).map((risk) => <div className="risk-row" key={risk}><AlertTriangle size={16}/><span>{risk}</span><span className="badge medium">Medium</span></div>)}</section>
        </aside>
      </div>
    </main>
  );
}

function KnowledgeView({ entries, lang }: { entries: KnowledgeEntry[]; lang: Lang }) {
  const text = copy[lang];
  return (
    <div className="knowledge-grid">
      {entries.map((entry) => (
        <article className="paper-card" key={entry.paper.id}>
          <div className="badges">{entry.tags.map((tag) => <span className="badge low" key={tag}>{tag}</span>)}</div>
          <div className="paper-title">{entry.paper.title}</div>
          <div className="meta">{entry.paper.primary_category} · {formatDate(entry.paper.published)} · updated {formatDate(entry.updated_at)}</div>
          {entry.key_takeaways.length > 0 && <ul className="evidence-list">{entry.key_takeaways.map((takeaway) => <li key={takeaway}>{takeaway}</li>)}</ul>}
          <p className="abstract">{entry.note || entry.paper.abstract}</p>
          <div className="actions"><a className="action" href={entry.paper.url} target="_blank">arXiv</a><a className="action" href={entry.paper.pdf_url} target="_blank"><FileText size={14}/>{text.pdf}</a></div>
        </article>
      ))}
      {entries.length === 0 && <EmptyState lang={lang}/>}
    </div>
  );
}

export default function Home() {
  const [lang, setLang] = useState<Lang>('en');
  const [view, setView] = useState<View>('radar');
  const [request, setRequest] = useState<SearchRequest>(initialRequest);
  const [payload, setPayload] = useState<SearchPayload>(initialPayload);
  const [knowledgeBase, setKnowledgeBase] = useState<Record<string, KnowledgeEntry>>({});
  const [categories, setCategories] = useState<Record<string, string>>(fallbackCategories);
  const [loading, setLoading] = useState(false);
  const [savingKnowledge, setSavingKnowledge] = useState(false);
  const [selected, setSelected] = useState<Recommendation | null>(null);
  const [query, setQuery] = useState('');
  const [priority, setPriority] = useState('all');
  const [status, setStatusFilter] = useState('all');
  const [notice, setNotice] = useState('');
  const text = copy[lang];

  useEffect(() => {
    const raw = window.localStorage.getItem('easy-parsing-session');
    if (!raw) return;
    try {
      const saved = JSON.parse(raw) as { payload?: SearchPayload; query?: string; lang?: Lang; request?: SearchRequest; knowledgeBase?: Record<string, KnowledgeEntry> };
      if (saved.payload?.recommendations) setPayload(saved.payload);
      if (saved.request) setRequest(saved.request);
      if (saved.knowledgeBase) setKnowledgeBase(saved.knowledgeBase);
      if (typeof saved.query === 'string') setQuery(saved.query);
      if (saved.lang === 'en' || saved.lang === 'zh') setLang(saved.lang);
    } catch {
      window.localStorage.removeItem('easy-parsing-session');
    }
  }, []);

  useEffect(() => {
    getMeta().then((meta) => {
      setCategories(meta.categories || fallbackCategories);
      setKnowledgeBase(meta.knowledge_base || {});
      setPayload((current) => applyStatuses(current, meta.reading_statuses || {}));
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    window.localStorage.setItem('easy-parsing-session', JSON.stringify({ payload, query, lang, request, knowledgeBase }));
  }, [payload, query, lang, request, knowledgeBase]);

  const recommendations = payload.recommendations;
  const knowledgeEntries = useMemo(() => Object.values(knowledgeBase).sort((a, b) => b.updated_at.localeCompare(a.updated_at)), [knowledgeBase]);
  const filtered = recommendations.filter((item) => {
    const kb = knowledgeBase[item.paper.id];
    const haystack = `${item.paper.title} ${item.paper.abstract} ${item.summary} ${item.reason} ${item.matched_keywords.join(' ')} ${item.matched_topics.join(' ')} ${kb?.note ?? ''} ${kb?.tags.join(' ') ?? ''}`.toLowerCase();
    return (!query || haystack.includes(query.toLowerCase())) && (priority === 'all' || item.priority === priority) && (status === 'all' || item.reading_status === status);
  });

  async function handleSearch() {
    setLoading(true);
    setNotice('');
    try {
      const result = await searchPapers({ ...request, query, language: lang });
      setPayload(result);
      setView('radar');
    } catch (error) {
      setNotice(lang === 'zh' ? `检索失败：${error instanceof Error ? error.message : String(error)}` : `Search failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleStatus(paperId: string, nextStatus: string) {
    setPayload((current) => ({ ...current, recommendations: current.recommendations.map((item) => item.paper.id === paperId ? { ...item, reading_status: nextStatus } : item) }));
    setSelected((current) => current && current.paper.id === paperId ? { ...current, reading_status: nextStatus } : current);
    try {
      await updatePaperStatus(paperId, nextStatus);
      setNotice('');
    } catch {
      setNotice(lang === 'zh' ? '已在当前页面更新状态；后端未连接，所以本次更改暂未持久化。' : 'Status updated locally; backend persistence failed.');
    }
  }

  async function handleSaveKnowledge(item: Recommendation, note: string, tags: string[], keyTakeaways: string[]) {
    setSavingKnowledge(true);
    try {
      const entry = await saveKnowledgeEntry(item.paper, note, tags, keyTakeaways);
      setKnowledgeBase((current) => ({ ...current, [item.paper.id]: entry }));
      await handleStatus(item.paper.id, item.reading_status === 'unread' ? 'saved' : item.reading_status);
      setNotice(text.savedKnowledge);
    } catch (error) {
      setNotice(lang === 'zh' ? `知识库保存失败：${error instanceof Error ? error.message : String(error)}` : `Knowledge save failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setSavingKnowledge(false);
    }
  }

  async function handleExport() {
    try {
      const path = await exportPayload(payload, 'markdown');
      setNotice(`${text.exported}: ${path}`);
    } catch {
      const markdown = payload.recommendations.map((item) => `### ${item.paper.title}\n- arXiv: ${item.paper.url}\n- PDF: ${item.paper.pdf_url}\n- Relevance: ${item.relevance_score}\n- Why: ${item.reason}`).join('\n\n');
      await navigator.clipboard?.writeText(`# Easy Parsing Digest\n\n${markdown}`);
      setNotice(lang === 'zh' ? '后端导出不可用，已将 Markdown 摘要复制到剪贴板。' : 'Backend export is unavailable; Markdown digest has been copied to clipboard.');
    }
  }

  function handleClearSession() {
    window.localStorage.removeItem('easy-parsing-session');
    setPayload(initialPayload);
    setSelected(null);
    setQuery('');
    setPriority('all');
    setStatusFilter('all');
    setView('radar');
    setNotice(text.sessionCleared);
  }

  const showUnavailable = () => setNotice(text.unavailable);
  if (selected) {
    return <DetailView item={selected} lang={lang} entry={knowledgeBase[selected.paper.id]} onBack={() => setSelected(null)} onStatus={handleStatus} onSaveKnowledge={handleSaveKnowledge} savingKnowledge={savingKnowledge} onUnavailable={showUnavailable}/>;
  }

  const viewFiltered = filtered.filter((item) => {
    if (view === 'radar') return item.priority === 'high' || item.relevance_score >= 70;
    if (view === 'discover') return !['saved', 'read_later', 'read', 'ignored'].includes(item.reading_status);
    if (view === 'library') return ['saved', 'read_later', 'read'].includes(item.reading_status);
    return true;
  });
  const functionalViews = ['radar', 'discover', 'library'].includes(view);
  const title = view === 'discover' ? (lang === 'zh' ? '发现新论文' : 'Discover New Papers') : view === 'library' ? text.queue : view === 'notes' ? text.knowledge : text.title;
  const placeholderTitle = view === 'alerts' ? (lang === 'zh' ? '提醒中心' : 'Alerts') : (lang === 'zh' ? '分析面板' : 'Analytics');
  const placeholderBody = view === 'alerts'
    ? (lang === 'zh' ? '未来会展示关键词订阅、作者更新和新论文提醒。' : 'Keyword subscriptions, author updates, and new-paper alerts will appear here.')
    : (lang === 'zh' ? '未来会展示阅读进度、主题分布和推荐质量趋势。' : 'Reading progress, topic distribution, and recommendation quality trends will appear here.');

  const mainContent = functionalViews ? (
    <>
      <div className="page-title"><h1>{title}</h1><span className="updated">• {text.updated} {formatTime(payload.generated_at)}</span></div>
      <MetricCards recommendations={view === 'library' ? viewFiltered : recommendations} knowledgeBase={knowledgeBase} lang={lang}/>
      <div className="section-head"><h2>{view === 'discover' ? (lang === 'zh' ? '待处理候选论文' : 'Unprocessed Candidates') : view === 'library' ? (lang === 'zh' ? '我的阅读库' : 'My Library') : text.top}</h2><button onClick={handleExport}>{text.export}</button></div>
      <div className="actions">
        <input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={text.search}/>
        <select className="action" value={priority} onChange={(event) => setPriority(event.target.value)}><option value="all">{text.priority}: {text.all}</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
        <select className="action" value={status} onChange={(event) => setStatusFilter(event.target.value)}><option value="all">{text.status}: {text.all}</option><option value="unread">Unread</option><option value="saved">Saved</option><option value="read_later">Read later</option><option value="read">Read</option><option value="ignored">Ignored</option></select>
        <button className="action primary" onClick={handleSearch}>{loading ? text.scanning : text.run}</button>
      </div>
      <div className="paper-list">{viewFiltered.map((item, index) => <PaperCard key={item.paper.id} item={item} index={index + 1} lang={lang} onSelect={setSelected} onStatus={handleStatus} onUnavailable={showUnavailable}/>)}</div>
      {viewFiltered.length === 0 && <EmptyState lang={lang}/>}
    </>
  ) : view === 'notes' ? (
    <>
      <div className="page-title"><h1>{text.knowledge}</h1><span className="updated">{knowledgeEntries.length} entries</span></div>
      <div className="actions"><input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={text.search}/></div>
      <KnowledgeView entries={knowledgeEntries.filter((entry) => !query || `${entry.paper.title} ${entry.note} ${entry.tags.join(' ')} ${entry.key_takeaways.join(' ')}`.toLowerCase().includes(query.toLowerCase()))} lang={lang}/>
    </>
  ) : (
    <section className="panel"><div className="panel-title"><span>{placeholderTitle}</span></div><p className="abstract">{placeholderBody}</p></section>
  );

  return (
    <div className="app-shell">
      <Sidebar lang={lang} setLang={setLang} view={view} setView={setView} request={request} setRequest={setRequest} onSearch={handleSearch} loading={loading} categories={categories}/>
      <main className="main">
        <div className="topbar">
          <input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={text.search}/>
          <div className="top-actions"><button className="link" onClick={handleClearSession}>{text.clearSession}</button><button className="link" onClick={() => setLang(lang === 'en' ? 'zh' : 'en')}>{lang === 'en' ? '中文' : 'EN'}</button><Bell size={18} onClick={showUnavailable}/><HelpCircle size={18} onClick={showUnavailable}/><div className="avatar"/></div>
        </div>
        {notice && <div className="panel"><div className="meta">{notice}</div></div>}
        <div className="dashboard"><section>{mainContent}</section><RightRail recommendations={recommendations} knowledgeBase={knowledgeBase} lang={lang} onViewAll={() => setView('library')}/></div>
      </main>
    </div>
  );
}
