from __future__ import annotations

import math
import re
from collections import Counter
from datetime import UTC, datetime

from src.models import Paper, Recommendation, ScoreBreakdown

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+\-_.]{1,}|[\u4e00-\u9fff]{2,}")
METHOD_TERMS = {
    "agent", "agents", "rag", "retrieval", "retrieval-augmented", "fine-tuning",
    "alignment", "benchmark", "evaluation", "dataset", "prompt", "reasoning",
    "code generation", "program repair", "test generation", "bug localization",
}
EXCLUDED_PAPER_TYPE_TERMS = {
    "survey", "review", "position paper", "perspective", "tutorial", "benchmark",
}
GENERIC_TERMS = {"ai", "artificial intelligence", "large language model", "large language models", "llm", "llms"}


class PaperRecommender:
    def recommend(
        self,
        papers: list[Paper],
        research_interest: str,
        positive_keywords: list[str],
        negative_keywords: list[str],
        language: str = "zh",
        selected_categories: list[str] | None = None,
        reading_statuses: dict[str, str] | None = None,
        hide_ignored: bool = True,
    ) -> list[Recommendation]:
        interest_terms = self._extract_terms(research_interest)
        positive_terms = self._dedupe_terms(self._normalize_terms(positive_keywords) + interest_terms)
        negative_terms = self._normalize_terms(negative_keywords)
        categories = selected_categories or []
        statuses = reading_statuses or {}
        recommendations = [
            self._score_paper(paper, positive_terms, interest_terms, negative_terms, categories, statuses, language)
            for paper in papers
        ]
        if hide_ignored:
            recommendations = [item for item in recommendations if item.reading_status != "ignored"]
        return sorted(recommendations, key=lambda item: item.relevance_score, reverse=True)

    def _score_paper(
        self,
        paper: Paper,
        positive_terms: list[str],
        interest_terms: list[str],
        negative_terms: list[str],
        selected_categories: list[str],
        reading_statuses: dict[str, str],
        language: str,
    ) -> Recommendation:
        title_lower = paper.title.lower()
        abstract_lower = paper.abstract.lower()
        combined_lower = f"{title_lower} {abstract_lower}"
        specific_positive_terms = [term for term in positive_terms if term not in GENERIC_TERMS]

        title_hits = sorted({term for term in specific_positive_terms if self._contains_term(title_lower, term)})
        abstract_hits = sorted({term for term in specific_positive_terms if self._contains_term(abstract_lower, term)})
        interest_hits = sorted({term for term in interest_terms if self._contains_term(combined_lower, term) and term not in GENERIC_TERMS})
        negative_hits = sorted({term for term in negative_terms if self._contains_term(combined_lower, term)})
        method_hits = sorted({term for term in METHOD_TERMS if self._contains_term(combined_lower, term)})
        excluded_type_hits = sorted({term for term in EXCLUDED_PAPER_TYPE_TERMS if self._contains_term(combined_lower, term)})
        category_match = not selected_categories or bool(set(paper.categories) & set(selected_categories))
        freshness_bonus = self._recency_bonus(paper)

        topic_score = min(35.0, 9.0 * len(title_hits) + 5.0 * len(abstract_hits) + 6.0 * len(interest_hits))
        method_score = min(20.0, 5.0 * len(method_hits))
        domain_score = 12.0 if category_match else 0.0
        evidence_strength = 12.0 if abstract_hits or interest_hits else (6.0 if title_hits else 2.0)
        reading_value = min(8.0, freshness_bonus * 3.0 + (2.0 if method_hits else 0.0))
        risk_penalty = min(22.0, 8.0 * len(negative_hits) + 4.0 * len(excluded_type_hits))
        normalized = max(0.0, min(100.0, topic_score + method_score + domain_score + evidence_strength + reading_value - risk_penalty))

        if normalized >= 78:
            priority = "high"
        elif normalized >= 50:
            priority = "medium"
        else:
            priority = "low"

        matched_positive = self._dedupe_terms(title_hits + abstract_hits + interest_hits + method_hits)
        breakdown = ScoreBreakdown(
            title_hits=title_hits,
            abstract_hits=abstract_hits,
            interest_hits=interest_hits,
            category_match=category_match,
            method_hits=method_hits,
            negative_hits=negative_hits,
            excluded_type_hits=excluded_type_hits,
            freshness_bonus=freshness_bonus,
            raw_score=normalized / 10,
        )
        evidence = self._make_evidence(paper, breakdown, language)
        risks = self._make_risks(breakdown, language)
        summary = self._make_summary(paper, matched_positive, language)
        reason = self._make_reason(normalized, breakdown, priority, language)

        return Recommendation(
            paper=paper,
            relevance_score=round(normalized, 1),
            priority=priority,
            matched_keywords=matched_positive,
            matched_exclusions=negative_hits,
            reason=reason,
            summary=summary,
            evidence=evidence,
            risks=risks,
            score_breakdown=breakdown,
            matched_topics=matched_positive[:10],
            mismatch_topics=negative_hits + excluded_type_hits,
            confidence=self._default_confidence(normalized, breakdown),
            paper_type=self._infer_paper_type(paper),
            recommended_action=self._recommended_action(normalized, priority),
            reading_status=reading_statuses.get(paper.id, "unread"),
        )

    @staticmethod
    def _normalize_terms(terms: list[str]) -> list[str]:
        return [term.strip().lower() for term in terms if term.strip()]

    @staticmethod
    def _dedupe_terms(terms: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for term in terms:
            if term and term not in seen:
                seen.add(term)
                deduped.append(term)
        return deduped

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        if not term:
            return False
        if re.search(r"[\u4e00-\u9fff]", term):
            return term in text
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None

    def _extract_terms(self, text: str) -> list[str]:
        stopwords = {
            "about", "with", "from", "into", "using", "based", "research", "paper",
            "large", "language", "model", "models", "especially", "application",
            "论文", "研究", "方向", "关于", "基于", "应用", "方法", "系统",
        }
        tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
        counts = Counter(token for token in tokens if token not in stopwords and len(token) > 1)
        return [term for term, _ in counts.most_common(16)]

    @staticmethod
    def _default_confidence(score: float, breakdown: ScoreBreakdown) -> str:
        if score >= 75 and (breakdown.abstract_hits or breakdown.interest_hits):
            return "high"
        if score >= 45 or breakdown.title_hits or breakdown.abstract_hits or breakdown.interest_hits:
            return "medium"
        return "low"

    @staticmethod
    def _infer_paper_type(paper: Paper) -> str:
        text = f"{paper.title} {paper.abstract}".lower()
        if "survey" in text or "review" in text:
            return "survey"
        if "benchmark" in text or "evaluation" in text or "evaluate" in text:
            return "benchmark"
        if "dataset" in text or "corpus" in text:
            return "dataset"
        if "framework" in text or "agenda" in text or "criteria" in text:
            return "framework"
        if "empirical" in text or "study" in text:
            return "empirical"
        if "method" in text or "algorithm" in text or "model" in text or "approach" in text:
            return "method"
        return "unknown"

    @staticmethod
    def _recommended_action(score: float, priority: str) -> str:
        if priority == "high" and score >= 82:
            return "read_now"
        if priority in {"high", "medium"} and score >= 55:
            return "skim"
        if score >= 35:
            return "save_for_later"
        return "ignore"
    @staticmethod
    def _recency_bonus(paper: Paper) -> float:
        if not paper.published:
            return 0.0
        age_days = (datetime.now(UTC) - paper.published).days
        return max(0.0, 1.2 - math.log1p(max(age_days, 0)) * 0.3)

    @staticmethod
    def _make_summary(paper: Paper, matched_terms: list[str], language: str) -> str:
        abstract = paper.abstract.strip()
        if len(abstract) > 520:
            abstract = abstract[:520].rsplit(" ", 1)[0] + "..."
        if language == "en":
            focus = ", ".join(matched_terms[:5]) if matched_terms else "the selected profile"
            return f"Abstract-based summary: {abstract} Relevance signal: potential connection to {focus}."
        focus = "、".join(matched_terms[:5]) if matched_terms else "当前研究画像"
        return f"基于摘要的总结：{abstract} 相关性信号：可能连接到 {focus}。"

    @staticmethod
    def _make_reason(score: float, breakdown: ScoreBreakdown, priority: str, language: str) -> str:
        if language == "en":
            priority_text = {"high": "high priority", "medium": "optional reading", "low": "low priority"}[priority]
            parts = [f"Recommended as {priority_text} with score {score:.1f}/100 based on profile overlap, method signals, category fit, evidence strength, and risk penalties."]
            matched = breakdown.title_hits + breakdown.abstract_hits + breakdown.interest_hits + breakdown.method_hits
            if matched:
                parts.append("Matched interests: " + ", ".join(matched[:6]) + ".")
            if breakdown.negative_hits or breakdown.excluded_type_hits:
                parts.append("Use caution because mismatch or paper-type risk signals were detected.")
            return " ".join(parts)
        priority_text = {"high": "重点阅读", "medium": "可选阅读", "low": "低优先级"}[priority]
        parts = [f"推荐等级为“{priority_text}”，评分 {score:.1f}/100；依据包括画像匹配、方法信号、分类匹配、证据强度和风险惩罚。"]
        matched = breakdown.title_hits + breakdown.abstract_hits + breakdown.interest_hits + breakdown.method_hits
        if matched:
            parts.append("匹配兴趣：" + "、".join(matched[:6]) + "。")
        if breakdown.negative_hits or breakdown.excluded_type_hits:
            parts.append("存在主题不匹配或论文类型风险，需要谨慎阅读。")
        return "".join(parts)

    @staticmethod
    def _make_evidence(paper: Paper, breakdown: ScoreBreakdown, language: str) -> list[str]:
        snippets: list[str] = []
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paper.abstract.strip()) if s.strip()]
        matched_terms = breakdown.title_hits + breakdown.abstract_hits + breakdown.interest_hits + breakdown.method_hits
        for sentence in sentences:
            lower = sentence.lower()
            if any(term in lower for term in matched_terms[:12]):
                snippets.append(sentence)
            if len(snippets) >= 4:
                break
        if not snippets and sentences:
            snippets = sentences[:2]
        if paper.primary_category:
            snippets.append(f"arXiv category: {paper.primary_category}" if language == "en" else f"arXiv 分类：{paper.primary_category}")
        return snippets or (["Insufficient evidence from title and abstract."] if language == "en" else ["标题和摘要中的证据不足。"])

    @staticmethod
    def _make_risks(breakdown: ScoreBreakdown, language: str) -> list[str]:
        risks: list[str] = []
        if language == "en":
            risks.append("Analysis is based only on title, abstract, and metadata; full-text experimental quality is not verified.")
            if breakdown.excluded_type_hits:
                risks.append("Paper type may require cautious reading: " + ", ".join(breakdown.excluded_type_hits))
            if breakdown.negative_hits:
                risks.append("Contains user-defined exclusion terms: " + ", ".join(breakdown.negative_hits))
            if not breakdown.abstract_hits and not breakdown.interest_hits:
                risks.append("The connection to the profile may be superficial or weakly supported by the abstract.")
            return risks
        risks.append("当前分析仅基于标题、摘要和元数据，尚未验证全文实验质量。")
        if breakdown.excluded_type_hits:
            risks.append("论文类型需要谨慎判断：" + "、".join(breakdown.excluded_type_hits))
        if breakdown.negative_hits:
            risks.append("包含用户设置的排除词：" + "、".join(breakdown.negative_hits))
        if not breakdown.abstract_hits and not breakdown.interest_hits:
            risks.append("与研究画像的连接可能较表层，摘要证据不足。")
        return risks

