"""Nettoyage d'une collecte JSON pour une seule source de presse."""

import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urldefrag, urlsplit

from gazette.models import Item

RULE_CLEAN_TEXT = "R-001"
RULE_FRESHNESS = "R-002"
RULE_REQUIRED_FIELDS = "R-003"
RULE_VALID_URL = "R-004"
RULE_FUTURE_DATE = "R-005"
RULE_ENCODING = "R-006"
RULE_SPONSORED_CONTENT = "R-007"
RULE_EXCLUDED_SECTION = "R-008"
RULE_EXACT_DUPLICATE = "R-009"
RULE_SIMILAR_TITLE = "R-010"

TRANSFORM_RULES = {
    RULE_CLEAN_TEXT: "Nettoyer le HTML et les espaces superflus",
    RULE_FRESHNESS: "Conserver les articles des dernières 24 heures",
    RULE_REQUIRED_FIELDS: "Vérifier le titre et le résumé",
    RULE_VALID_URL: "Vérifier l'URL HTTP(S)",
    RULE_FUTURE_DATE: "Rejeter les dates futures",
    RULE_ENCODING: "Rejeter les encodages cassés",
    RULE_SPONSORED_CONTENT: "Rejeter les publi-reportages et contenus partenaires",
    RULE_EXCLUDED_SECTION: "Rejeter les horoscopes, programmes TV, jeux et concours",
    RULE_EXACT_DUPLICATE: "Rejeter les doublons exacts",
    RULE_SIMILAR_TITLE: "Rejeter les titres très similaires",
}

SPONSORED_CONTENT_PATTERNS = (
    r"\bpubli[- ]?reportage\b",
    r"\bcontenu(?:s)? partenaire(?:s)?\b",
)
EXCLUDED_SECTION_PATTERNS = (
    r"\bhoroscope\b",
    r"\bprogramme(?:s)?\s*(?:tv|télé(?:visé)?(?:s)?)\b",
    r"\bjeux?\b",
    r"\bconcours\b",
)
BROKEN_ENCODING_MARKERS = ("�", "Ã", "Â", "â€™", "â€œ", "â€")
SPONSORED_CONTENT_RE = re.compile("|".join(SPONSORED_CONTENT_PATTERNS), re.IGNORECASE)
EXCLUDED_SECTION_RE = re.compile("|".join(EXCLUDED_SECTION_PATTERNS), re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class TransformReport:
    """Résultats d'un passage de transformation pour une source."""

    input_count: int
    kept_count: int
    rejected_by_rule: dict[str, int]

    @property
    def rejected_count(self) -> int:
        return self.input_count - self.kept_count


def read_raw_json(path: Path, source: str) -> list[Item]:
    """Lit une collecte JSON et vérifie qu'elle correspond à la source demandée."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("source") != source:
        raise ValueError(
            f"Le fichier {path} contient la source {data.get('source')!r}, pas {source!r}"
        )

    items = []
    for raw_item in data.get("items", []):
        published_at = raw_item.get("published_at")
        items.append(
            Item(
                source=raw_item["source"],
                title=raw_item["title"],
                summary=raw_item.get("summary", ""),
                url=raw_item["url"],
                published_at=datetime.fromisoformat(published_at) if published_at else None,
            )
        )
    return items


def transform_items(
    items: list[Item],
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> list[Item]:
    """Nettoie et dédoublonne les articles d'une source sur les dernières 24 heures."""
    transformed, _ = transform_items_with_report(items, now=now, max_age=max_age)
    return transformed


def transform_items_with_report(
    items: list[Item],
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> tuple[list[Item], TransformReport]:
    """Transforme les articles et compte les rejets par identifiant de règle."""
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    cutoff = reference - max_age

    transformed = []
    rejected = Counter[str]()

    def reject(rule: str) -> None:
        rejected[rule] += 1

    seen_urls: set[str] = set()
    seen_titles: list[list[str]] = []
    for item in items:
        title = _normalize_text(item.title)
        summary = _normalize_text(item.summary)
        if not title or not summary:
            reject(RULE_REQUIRED_FIELDS)
            continue
        if _contains_broken_encoding(title) or _contains_broken_encoding(summary):
            reject(RULE_ENCODING)
            continue
        content = f"{title} {summary}"
        if SPONSORED_CONTENT_RE.search(content):
            reject(RULE_SPONSORED_CONTENT)
            continue
        if EXCLUDED_SECTION_RE.search(content):
            reject(RULE_EXCLUDED_SECTION)
            continue

        url = urldefrag(item.url.strip()).url
        parsed_url = urlsplit(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            reject(RULE_VALID_URL)
            continue

        if item.published_at is None:
            reject(RULE_FRESHNESS)
            continue
        published_at = item.published_at
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)
        if published_at < cutoff:
            reject(RULE_FRESHNESS)
            continue
        if published_at > reference:
            reject(RULE_FUTURE_DATE)
            continue

        title_tokens = _title_tokens(title)
        has_similar_title = any(
            _titles_are_similar(title_tokens, previous) for previous in seen_titles
        )
        if url in seen_urls:
            reject(RULE_EXACT_DUPLICATE)
            continue
        if has_similar_title:
            reject(RULE_SIMILAR_TITLE)
            continue
        seen_urls.add(url)
        seen_titles.append(title_tokens)
        transformed.append(
            Item(
                source=item.source,
                title=title,
                summary=summary,
                url=url,
                published_at=published_at,
            )
        )
    report = TransformReport(
        input_count=len(items),
        kept_count=len(transformed),
        rejected_by_rule={
            rule: rejected.get(rule, 0) for rule in TRANSFORM_RULES if rule != RULE_CLEAN_TEXT
        },
    )
    return transformed, report


def _normalize_text(value: str) -> str:
    value = HTML_TAG_RE.sub(" ", html.unescape(value))
    return re.sub(r"\s+", " ", value).strip()


def _contains_broken_encoding(value: str) -> bool:
    return any(marker in value for marker in BROKEN_ENCODING_MARKERS)


def _title_tokens(title: str) -> list[str]:
    return re.findall(r"\w+", title.casefold())


def _titles_are_similar(left: list[str], right: list[str]) -> bool:
    if not left or not right:
        return False
    common = len(set(left) & set(right))
    difference = len(set(left) ^ set(right))
    return common >= 2 and difference <= 2
