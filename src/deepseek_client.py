from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests

from src.models import Recommendation

DEEPSEEK_BASE_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
ADVANCED_DEEPSEEK_MODEL = "deepseek-v4-pro"


@dataclass
class DeepSeekConfig:
    api_key: str = ""
    model: str = DEFAULT_DEEPSEEK_MODEL
    base_url: str = DEEPSEEK_BASE_URL
    timeout: int = 45
    max_items: int = 12

    @classmethod
    def from_env(cls) -> "DeepSeekConfig":
        return cls(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            model=os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
            base_url=os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL),
        )


class DeepSeekPaperJudge:
    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        self.config = config or DeepSeekConfig.from_env()

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key.strip())

    def refine_recommendations(
        self,
        recommendations: list[Recommendation],
        research_interest: str,
        positive_keywords: list[str],
        negative_keywords: list[str],
        language: str,
    ) -> list[Recommendation]:
        if not self.is_configured:
            return recommendations

        target_items, untouched_items = self._select_review_pool(recommendations)
        refined: list[Recommendation] = []

        for item in target_items:
            try:
                judgement = self._judge_one(item, research_interest, positive_keywords, negative_keywords, language)
            except requests.RequestException as exc:
                item.risks.append(self._api_risk_message(str(exc), language))
                refined.append(item)
                continue
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                item.risks.append(self._parse_risk_message(str(exc), language))
                refined.append(item)
                continue

            self._apply_judgement(item, judgement)
            refined.append(item)

        return sorted(refined + untouched_items, key=lambda entry: entry.relevance_score, reverse=True)

    def _select_review_pool(self, recommendations: list[Recommendation]) -> tuple[list[Recommendation], list[Recommendation]]:
        if not recommendations:
            return [], []

        limit = max(1, self.config.max_items)
        high_confidence = recommendations[: max(1, int(limit * 0.5))]
        uncertain = [item for item in recommendations if 35 <= item.relevance_score < 75]
        exploratory = [item for item in recommendations if item.relevance_score < 35 and item.matched_keywords]

        selected: list[Recommendation] = []
        seen: set[str] = set()
        for group in (high_confidence, uncertain, exploratory):
            for item in group:
                if item.paper.id in seen:
                    continue
                selected.append(item)
                seen.add(item.paper.id)
                if len(selected) >= limit:
                    break
            if len(selected) >= limit:
                break

        untouched = [item for item in recommendations if item.paper.id not in seen]
        return selected, untouched

    def _judge_one(
        self,
        item: Recommendation,
        research_interest: str,
        positive_keywords: list[str],
        negative_keywords: list[str],
        language: str,
    ) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self._system_prompt(language)},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "user_research_profile": {
                                "research_interest": research_interest,
                                "positive_keywords": positive_keywords,
                                "negative_keywords_or_excluded_topics": negative_keywords,
                            },
                            "paper_metadata": item.paper.to_dict(),
                            "retrieval_signals_for_auxiliary_reference_only": {
                                "rule_based_candidate_score": item.relevance_score,
                                "rule_based_priority": item.priority,
                                "matched_topics": item.matched_topics,
                                "mismatch_topics": item.mismatch_topics,
                            },
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.config.base_url, headers=headers, json=payload, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    @staticmethod
    def _system_prompt(language: str) -> str:
        output_language = "Chinese" if language == "zh" else "English"
        return (
            "You are a careful research-paper triage assistant for academic researchers. "
            "Your task is to judge whether an arXiv paper is relevant to the user's research profile. "
            "Use only the provided title, abstract, arXiv categories, and supplied rule-based retrieval signals. "
            "Do not use outside knowledge. Do not invent facts, methods, results, datasets, benchmarks, venues, code availability, or claims. "
            "If the provided information is insufficient, explicitly say so in the risks field. "
            "Rule-based retrieval signals may help inform scoring, but they are not paper evidence. "
            "Keyword-match logs, recency bonuses, category-match logs, and internal scoring features must not be copied into the evidence field. "
            "Evidence must be grounded in the paper title, abstract, or arXiv categories. "
            "Evaluate relevance based on match to core interests, preferred methods/tasks/domains, excluded topics, centrality, evidence strength, and paper type. "
            "Scoring guide: 90-100 = highly relevant, centrally aligned, and likely worth reading soon; "
            "70-89 = clearly relevant and worth saving or skimming; "
            "40-69 = partially or tangentially relevant; "
            "0-39 = mostly irrelevant, excluded, or insufficiently related. "
            "A score above 85 requires specific alignment with the user's core interests, tasks, methods, or domain. "
            "A score above 90 requires direct central relevance and strong abstract-level evidence. "
            "Do not assign high priority only because of broad terms such as AI, LLM, agent, benchmark, learning, or evaluation. "
            "arXiv categories are weak supporting signals and are not sufficient for high relevance by themselves. "
            "Priority guide: high = strong match with clear evidence; medium = useful but not central or relevant with uncertainty; low = weak, unrelated, excluded, or too little evidence. "
            "Confidence guide: high = title and abstract provide specific direct evidence; medium = relevant but important details are missing; low = broad terms, weak signals, or insufficient metadata. "
            "Be conservative. Explicitly distinguish central relevance from superficial keyword overlap. "
            "Do not fill any field with generic placeholder text. Do not merely copy or truncate the abstract. "
            "If a field cannot be answered from the title and abstract, explicitly state that evidence is insufficient. "
            "Return strict JSON only. Do not include markdown, comments, or extra text. "
            "The JSON object must contain exactly these keys: "
            "llm_score, priority, confidence, paper_type, recommended_action, summary, reason, evidence, risks, matched_topics, mismatch_topics. "
            "Field requirements: llm_score: a number from 0 to 100; "
            "priority: one of 'high', 'medium', or 'low'; "
            "confidence: one of 'high', 'medium', or 'low'; "
            "paper_type: one of 'method', 'benchmark', 'survey', 'dataset', 'empirical', 'framework', 'position', 'application', or 'unknown'; "
            "recommended_action: one of 'read_now', 'skim', 'save_for_later', or 'ignore'; "
            "summary: 1-2 concise sentences summarizing the apparent research problem and main idea; "
            "reason: mention the strongest relevance signal and strongest uncertainty or mismatch when present; "
            "evidence: an array of short strings quoting or faithfully paraphrasing only the title, abstract, or arXiv categories; "
            "risks: an array describing uncertainty, missing information, possible mismatch, or reliability limits; "
            "matched_topics: an array of supported user-relevant topics, tasks, domains, or methods; "
            "mismatch_topics: an array of topics, domains, paper types, or missing aspects that weaken the match. "
            f"Use {output_language} for summary, reason, evidence, risks, matched_topics, and mismatch_topics."
        )

    @staticmethod
    def _apply_judgement(item: Recommendation, judgement: dict[str, Any]) -> None:
        llm_score = float(judgement.get("llm_score", item.relevance_score))
        item.relevance_score = round(max(0.0, min(100.0, llm_score)), 1)

        priority = str(judgement.get("priority", item.priority)).lower()
        item.priority = priority if priority in {"high", "medium", "low"} else item.priority

        confidence = str(judgement.get("confidence", item.confidence)).lower()
        item.confidence = confidence if confidence in {"high", "medium", "low"} else item.confidence

        paper_type = str(judgement.get("paper_type", item.paper_type)).lower()
        item.paper_type = paper_type if paper_type in {"method", "benchmark", "survey", "dataset", "empirical", "framework", "position", "application", "unknown"} else item.paper_type

        action = str(judgement.get("recommended_action", item.recommended_action)).lower()
        item.recommended_action = action if action in {"read_now", "skim", "save_for_later", "ignore"} else item.recommended_action

        item.summary = str(judgement.get("summary") or item.summary)
        item.reason = str(judgement.get("reason") or item.reason)

        evidence = judgement.get("evidence")
        if isinstance(evidence, list) and evidence:
            item.evidence = [str(entry) for entry in evidence[:8]]
        risks = judgement.get("risks")
        if isinstance(risks, list) and risks:
            item.risks = [str(entry) for entry in risks[:8]]
        matched_topics = judgement.get("matched_topics")
        if isinstance(matched_topics, list):
            item.matched_topics = [str(entry) for entry in matched_topics[:10]]
        mismatch_topics = judgement.get("mismatch_topics")
        if isinstance(mismatch_topics, list):
            item.mismatch_topics = [str(entry) for entry in mismatch_topics[:10]]

    @staticmethod
    def _api_risk_message(message: str, language: str) -> str:
        if language == "en":
            return f"DeepSeek triage failed due to API/network error; kept rule-based candidate result. Detail: {message}"
        return f"DeepSeek 学术筛选因 API 或网络错误失败，已保留规则候选结果。细节：{message}"

    @staticmethod
    def _parse_risk_message(message: str, language: str) -> str:
        if language == "en":
            return f"DeepSeek response could not be parsed; kept rule-based candidate result. Detail: {message}"
        return f"DeepSeek 返回无法解析，已保留规则候选结果。细节：{message}"
