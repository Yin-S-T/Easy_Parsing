from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET

import requests

from src.models import Paper

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache" / "arxiv"


class ArxivClientError(RuntimeError):
    pass


class ArxivClient:
    def __init__(self, timeout: int = 30, retries: int = 3, cache_ttl_seconds: int = 6 * 60 * 60) -> None:
        self.timeout = timeout
        self.retries = retries
        self.cache_ttl_seconds = cache_ttl_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "EasyParsing/0.2 (local research assistant; contact: local@example.com)",
                "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
            }
        )

    def search_recent(
        self,
        categories: Iterable[str],
        max_results: int = 50,
        days_back: int = 14,
        query: str = "",
    ) -> list[Paper]:
        requested_max = max(1, min(int(max_results), 300))
        page_size = min(100, max(25, requested_max))
        cutoff = datetime.now(UTC) - timedelta(days=max(days_back, 1))
        category_query = " OR ".join(f"cat:{category.strip()}" for category in categories if category.strip())
        if not category_query:
            category_query = "cat:cs.AI"

        keyword_query = self._build_keyword_query(query)
        search_query = f"({category_query}) AND ({keyword_query})" if keyword_query else category_query

        papers: list[Paper] = []
        seen: set[str] = set()
        for start in range(0, requested_max, page_size):
            params = {
                "search_query": search_query,
                "start": start,
                "max_results": min(page_size, requested_max - start),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            xml_text, from_cache = self._get_text_with_cache(params)
            page = self._parse_atom_feed(xml_text)
            if not page:
                break

            for paper in page:
                if not paper.published or paper.published < cutoff or paper.id in seen:
                    continue
                papers.append(paper)
                seen.add(paper.id)
                if len(papers) >= requested_max:
                    return papers

            if all(paper.published and paper.published < cutoff for paper in page):
                break
            if not from_cache:
                time.sleep(0.6)

        return papers

    def _get_text_with_cache(self, params: dict[str, object]) -> tuple[str, bool]:
        cache_key = self._cache_key(params)
        cache_path = ARXIV_CACHE_DIR / f"{cache_key}.json"
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached, True

        response = self._get_with_retry(params)
        self._write_cache(cache_path, response.text)
        return response.text, False

    def _get_with_retry(self, params: dict[str, object]) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(ARXIV_API_URL, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(1.5 * (attempt + 1))
        raise ArxivClientError(f"arXiv request failed after {self.retries} attempts: {last_error}")

    def _parse_atom_feed(self, xml_text: str) -> list[Paper]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ArxivClientError(f"Invalid arXiv response XML: {exc}") from exc
        papers: list[Paper] = []

        for entry in root.findall("atom:entry", ATOM_NAMESPACE):
            entry_id = self._safe_text(entry.find("atom:id", ATOM_NAMESPACE))
            title = self._normalize_whitespace(self._safe_text(entry.find("atom:title", ATOM_NAMESPACE)))
            abstract = self._normalize_whitespace(self._safe_text(entry.find("atom:summary", ATOM_NAMESPACE)))
            published = self._parse_datetime(self._safe_text(entry.find("atom:published", ATOM_NAMESPACE)))
            updated = self._parse_datetime(self._safe_text(entry.find("atom:updated", ATOM_NAMESPACE)))
            authors = [
                self._normalize_whitespace(self._safe_text(author.find("atom:name", ATOM_NAMESPACE)))
                for author in entry.findall("atom:author", ATOM_NAMESPACE)
            ]
            categories = [category.attrib.get("term", "") for category in entry.findall("atom:category", ATOM_NAMESPACE)]
            primary_category = categories[0] if categories else "unknown"
            pdf_url = self._extract_pdf_url(entry) or entry_id.replace("abs", "pdf") + ".pdf"

            papers.append(
                Paper(
                    id=entry_id,
                    title=title,
                    abstract=abstract,
                    authors=[name for name in authors if name],
                    published=published,
                    updated=updated,
                    categories=[c for c in categories if c],
                    primary_category=primary_category,
                    url=entry_id,
                    pdf_url=pdf_url,
                )
            )

        return papers

    @staticmethod
    def _build_keyword_query(query: str) -> str:
        terms = [term for term in re.split(r"[,;\n]+", query.strip()) if term.strip()]
        cleaned = []
        for term in terms[:8]:
            safe = re.sub(r"[^\w\s\-]", " ", term).strip()
            if safe:
                cleaned.append(f'all:"{safe}"')
        return " OR ".join(cleaned)

    def _read_cache(self, path: Path) -> str | None:
        if self.cache_ttl_seconds <= 0 or not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            created_at = datetime.fromisoformat(data.get("created_at", ""))
            if (datetime.now(UTC) - created_at).total_seconds() > self.cache_ttl_seconds:
                return None
            text = data.get("text")
            return text if isinstance(text, str) and text.strip() else None
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _write_cache(path: Path, text: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"created_at": datetime.now(UTC).isoformat(), "text": text}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            return

    @staticmethod
    def _cache_key(params: dict[str, object]) -> str:
        raw = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _safe_text(element: ET.Element | None) -> str:
        return element.text.strip() if element is not None and element.text else ""

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _extract_pdf_url(entry: ET.Element) -> str | None:
        for link in entry.findall("atom:link", ATOM_NAMESPACE):
            href = link.attrib.get("href")
            title = link.attrib.get("title", "")
            if title.lower() == "pdf" and href:
                return href
        return None
