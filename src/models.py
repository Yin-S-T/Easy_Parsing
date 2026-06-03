from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Paper:
    id: str
    title: str
    abstract: str
    authors: list[str]
    published: datetime | None
    updated: datetime | None
    categories: list[str]
    primary_category: str
    url: str
    pdf_url: str
    source: str = "arxiv"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "published": self.published.isoformat() if self.published else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "categories": self.categories,
            "primary_category": self.primary_category,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "source": self.source,
        }


@dataclass
class ScoreBreakdown:
    title_hits: list[str] = field(default_factory=list)
    abstract_hits: list[str] = field(default_factory=list)
    interest_hits: list[str] = field(default_factory=list)
    category_match: bool = False
    method_hits: list[str] = field(default_factory=list)
    negative_hits: list[str] = field(default_factory=list)
    excluded_type_hits: list[str] = field(default_factory=list)
    freshness_bonus: float = 0.0
    raw_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "title_hits": self.title_hits,
            "abstract_hits": self.abstract_hits,
            "interest_hits": self.interest_hits,
            "category_match": self.category_match,
            "method_hits": self.method_hits,
            "negative_hits": self.negative_hits,
            "excluded_type_hits": self.excluded_type_hits,
            "freshness_bonus": round(self.freshness_bonus, 2),
            "raw_score": round(self.raw_score, 2),
        }


@dataclass
class Recommendation:
    paper: Paper
    relevance_score: float
    priority: str
    matched_keywords: list[str] = field(default_factory=list)
    matched_exclusions: list[str] = field(default_factory=list)
    reason: str = ""
    summary: str = ""
    evidence: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    score_breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    matched_topics: list[str] = field(default_factory=list)
    mismatch_topics: list[str] = field(default_factory=list)
    confidence: str = "medium"
    paper_type: str = "unknown"
    recommended_action: str = "skim"
    reading_status: str = "unread"

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper": self.paper.to_dict(),
            "relevance_score": self.relevance_score,
            "priority": self.priority,
            "matched_keywords": self.matched_keywords,
            "matched_exclusions": self.matched_exclusions,
            "reason": self.reason,
            "summary": self.summary,
            "evidence": self.evidence,
            "risks": self.risks,
            "score_breakdown": self.score_breakdown.to_dict(),
            "matched_topics": self.matched_topics,
            "mismatch_topics": self.mismatch_topics,
            "confidence": self.confidence,
            "paper_type": self.paper_type,
            "recommended_action": self.recommended_action,
            "reading_status": self.reading_status,
        }
