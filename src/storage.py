from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

EXPORT_DIR = Path(__file__).resolve().parents[1] / "data" / "exports"
STATE_DIR = Path(__file__).resolve().parents[1] / "data" / "state"
READING_STATUS_PATH = STATE_DIR / "reading_status.json"
KNOWLEDGE_BASE_PATH = STATE_DIR / "knowledge_base.json"
VALID_READING_STATUSES = {"unread", "saved", "read_later", "read", "ignored"}


def save_recommendations(payload: dict[str, Any], export_format: str = "json") -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    normalized_format = export_format.lower()

    if normalized_format == "markdown":
        path = EXPORT_DIR / f"recommendations_{timestamp}.md"
        path.write_text(_payload_to_markdown(payload), encoding="utf-8")
        return path

    if normalized_format == "bibtex":
        path = EXPORT_DIR / f"recommendations_{timestamp}.bib"
        path.write_text(_payload_to_bibtex(payload), encoding="utf-8")
        return path

    path = EXPORT_DIR / f"recommendations_{timestamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_reading_statuses() -> dict[str, str]:
    if not READING_STATUS_PATH.exists():
        return {}
    try:
        data = json.loads(READING_STATUS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        str(paper_id): status
        for paper_id, status in data.items()
        if status in VALID_READING_STATUSES
    }


def update_reading_status(paper_id: str, status: str) -> dict[str, str]:
    if status not in VALID_READING_STATUSES:
        raise ValueError(f"Unsupported reading status: {status}")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    statuses = load_reading_statuses()
    statuses[paper_id] = status
    READING_STATUS_PATH.write_text(json.dumps(statuses, ensure_ascii=False, indent=2), encoding="utf-8")
    return statuses


def load_knowledge_base() -> dict[str, dict[str, Any]]:
    if not KNOWLEDGE_BASE_PATH.exists():
        return {}
    try:
        data = json.loads(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(paper_id): entry
        for paper_id, entry in data.items()
        if isinstance(entry, dict) and isinstance(entry.get("paper"), dict)
    }


def upsert_knowledge_entry(
    paper: dict[str, Any],
    note: str = "",
    tags: list[str] | None = None,
    key_takeaways: list[str] | None = None,
) -> dict[str, Any]:
    paper_id = str(paper.get("id") or paper.get("url") or "").strip()
    if not paper_id:
        raise ValueError("Knowledge entry requires paper.id or paper.url")

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    knowledge = load_knowledge_base()
    existing = knowledge.get(paper_id, {})
    now = datetime.now().isoformat()
    created_at = str(existing.get("created_at") or now)
    merged_tags = _clean_list(tags if tags is not None else existing.get("tags", []))
    merged_takeaways = _clean_list(key_takeaways if key_takeaways is not None else existing.get("key_takeaways", []))

    entry = {
        "paper": {**existing.get("paper", {}), **paper},
        "note": note if note or "note" not in existing else str(existing.get("note", "")),
        "tags": merged_tags,
        "key_takeaways": merged_takeaways,
        "created_at": created_at,
        "updated_at": now,
    }
    knowledge[paper_id] = entry
    KNOWLEDGE_BASE_PATH.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def delete_knowledge_entry(paper_id: str) -> dict[str, dict[str, Any]]:
    knowledge = load_knowledge_base()
    knowledge.pop(paper_id, None)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_BASE_PATH.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2), encoding="utf-8")
    return knowledge


def _payload_to_markdown(payload: dict[str, Any]) -> str:
    generated_at = payload.get("generated_at", "")
    recommendations = payload.get("recommendations", [])
    lines = ["# Easy Parsing Recommendations", "", f"Generated at: {generated_at}", ""]

    for item in recommendations:
        paper = item.get("paper", {})
        lines.extend([
            f"## {paper.get('title', 'Untitled')}",
            "",
            f"- Score: {item.get('relevance_score', '-')}",
            f"- Priority: {item.get('priority', '-')}",
            f"- Status: {item.get('reading_status', 'unread')}",
            f"- Authors: {', '.join(paper.get('authors', [])) or '-'}",
            f"- Published: {paper.get('published') or '-'}",
            f"- Categories: {', '.join(paper.get('categories', [])) or '-'}",
            f"- URL: {paper.get('url') or '-'}",
            f"- PDF: {paper.get('pdf_url') or '-'}",
            "",
            f"**Reason:** {item.get('reason', '')}",
            "",
            f"**Summary:** {item.get('summary', '')}",
            "",
        ])
        evidence = item.get("evidence", [])
        if evidence:
            lines.append("**Evidence:**")
            lines.extend(f"- {entry}" for entry in evidence)
            lines.append("")
        risks = item.get("risks", [])
        if risks:
            lines.append("**Risks:**")
            lines.extend(f"- {entry}" for entry in risks)
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in seen:
            cleaned.append(item)
            seen.add(item)
    return cleaned[:20]


def _payload_to_bibtex(payload: dict[str, Any]) -> str:
    entries = []
    for item in payload.get("recommendations", []):
        paper = item.get("paper", {})
        title = paper.get("title", "Untitled")
        authors = " and ".join(paper.get("authors", [])) or "Unknown"
        published = paper.get("published") or ""
        year = published[:4] if published else ""
        key = _bibtex_key(authors, title, year)
        entries.append(
            "\n".join([
                f"@misc{{{key},",
                f"  title = {{{_escape_bibtex(title)}}},",
                f"  author = {{{_escape_bibtex(authors)}}},",
                f"  year = {{{year}}},",
                f"  eprint = {{{paper.get('id', '')}}},",
                "  archivePrefix = {arXiv},",
                f"  primaryClass = {{{paper.get('primary_category', '')}}},",
                f"  url = {{{paper.get('url', '')}}}",
                "}",
            ])
        )
    return "\n\n".join(entries).strip() + "\n"


def _bibtex_key(authors: str, title: str, year: str) -> str:
    first_author = authors.split(" and ")[0].split(",")[0].split()[-1] if authors else "paper"
    title_word_match = re.search(r"[A-Za-z0-9]+", title)
    title_word = title_word_match.group(0) if title_word_match else "paper"
    key = f"{first_author}{year}{title_word}"
    return re.sub(r"[^A-Za-z0-9]", "", key) or "easypaper"


def _escape_bibtex(value: str) -> str:
    return value.replace("{", "\\{").replace("}", "\\}")

