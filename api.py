from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        env_path = Path(__file__).resolve().parent / ".env"
        if not env_path.exists():
            return False
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return True

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.arxiv_client import ArxivClient, ArxivClientError
from src.deepseek_client import DEFAULT_DEEPSEEK_MODEL, DeepSeekConfig, DeepSeekPaperJudge
from src.i18n import ARXIV_CS_CATEGORIES, split_keywords
from src.recommender import PaperRecommender
from src.storage import load_knowledge_base, load_reading_statuses, save_recommendations, update_reading_status, upsert_knowledge_entry

load_dotenv()

app = FastAPI(title="Easy Parsing API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    language: str = Field(default="en", pattern="^(en|zh)$")
    research_interest: str = Field(default="", max_length=4000)
    positive_keywords: str = Field(default="", max_length=1200)
    negative_keywords: str = Field(default="", max_length=1200)
    categories: list[str] = Field(default_factory=lambda: ["cs.AI", "cs.CL", "cs.LG", "cs.SE"], min_length=1, max_length=16)
    days_back: int = Field(default=30, ge=1, le=180)
    max_results: int = Field(default=80, ge=1, le=300)
    query: str = Field(default="", max_length=1200)
    use_ai_review: bool = False
    llm_max_items: int = Field(default=16, ge=0, le=50)


class StatusRequest(BaseModel):
    paper_id: str = Field(min_length=1, max_length=600)
    status: str = Field(pattern="^(unread|saved|read_later|read|ignored)$")


class ExportRequest(BaseModel):
    payload: dict[str, Any]
    export_format: str = Field(default="markdown", pattern="^(markdown|json|bibtex)$")


class KnowledgeRequest(BaseModel):
    paper: dict[str, Any]
    note: str = Field(default="", max_length=20000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    key_takeaways: list[str] = Field(default_factory=list, max_length=20)


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    config = DeepSeekConfig.from_env()
    return {
        "categories": ARXIV_CS_CATEGORIES,
        "reading_statuses": load_reading_statuses(),
        "knowledge_base": load_knowledge_base(),
        "default_model": DEFAULT_DEEPSEEK_MODEL,
        "ai_review_configured": bool(config.api_key.strip()),
    }


@app.post("/api/search")
def search(req: SearchRequest) -> dict[str, Any]:
    invalid_categories = sorted(set(req.categories) - set(ARXIV_CS_CATEGORIES.values()))
    if invalid_categories:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_CATEGORIES",
                "message": f"Unsupported arXiv categories: {', '.join(invalid_categories)}",
            },
        )

    statuses = load_reading_statuses()
    try:
        papers = ArxivClient().search_recent(
            categories=req.categories,
            max_results=req.max_results,
            days_back=req.days_back,
            query=req.query,
        )
    except ArxivClientError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ARXIV_UNAVAILABLE",
                "message": "arXiv is temporarily unavailable or blocked by the current network. Please retry later or reduce the query scope.",
                "raw_error": str(exc),
            },
        ) from exc

    recommendations = PaperRecommender().recommend(
        papers=papers,
        research_interest=req.research_interest,
        positive_keywords=split_keywords(req.positive_keywords),
        negative_keywords=split_keywords(req.negative_keywords),
        language=req.language,
        selected_categories=req.categories,
        reading_statuses=statuses,
    )
    if req.use_ai_review:
        config = DeepSeekConfig.from_env()
        config.max_items = req.llm_max_items
        judge = DeepSeekPaperJudge(config)
        if judge.is_configured:
            recommendations = judge.refine_recommendations(
                recommendations=recommendations,
                research_interest=req.research_interest,
                positive_keywords=split_keywords(req.positive_keywords),
                negative_keywords=split_keywords(req.negative_keywords),
                language=req.language,
            )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "config": req.model_dump(),
        "recommendations": [item.to_dict() for item in recommendations],
    }
    return payload


@app.post("/api/status")
def update_status(req: StatusRequest) -> dict[str, Any]:
    try:
        statuses = update_reading_status(req.paper_id, req.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_STATUS", "message": str(exc)}) from exc
    return {"reading_statuses": statuses}


@app.post("/api/export")
def export(req: ExportRequest) -> dict[str, str]:
    path = save_recommendations(req.payload, req.export_format)
    return {"path": str(path)}


@app.get("/api/knowledge")
def knowledge() -> dict[str, Any]:
    entries = load_knowledge_base()
    return {
        "entries": entries,
        "count": len(entries),
    }


@app.post("/api/knowledge")
def save_knowledge(req: KnowledgeRequest) -> dict[str, Any]:
    try:
        entry = upsert_knowledge_entry(
            paper=req.paper,
            note=req.note,
            tags=req.tags,
            key_takeaways=req.key_takeaways,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_KNOWLEDGE_ENTRY", "message": str(exc)}) from exc
    return {"entry": entry, "knowledge_base": load_knowledge_base()}
