"""Collecte : lire le flux RSS d'une source et en extraire les items.

On ne garde que le titre, l'extrait, le lien, la date et la source (docs/cadrage.md).
Le champ auteur présent dans certains flux (La Croix, Libération...) n'est jamais repris.
"""

import calendar
import json
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import feedparser

from gazette.models import Item
from gazette.sources import Source


class CollectError(Exception):
    """La source n'a pas pu être lue : accès refusé, réseau, flux illisible."""


def http_get(url: str, user_agent: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def robots_allows(robots_txt: str, url: str, user_agent: str) -> bool:
    """Dit si robots.txt autorise notre User-Agent à lire cette adresse.

    Limite connue : le module standard ne gère pas les jokers (*) dans les chemins.
    """
    parser = RobotFileParser()
    parser.parse(robots_txt.splitlines())
    return parser.can_fetch(user_agent, url)


def check_robots(url: str, user_agent: str, timeout: float) -> None:
    """Lève CollectError si robots.txt interdit la lecture ou ne peut pas être vérifié."""
    robots_url = urljoin(url, "/robots.txt")
    try:
        robots_txt = http_get(robots_url, user_agent, timeout).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        # Même règle que le module standard : 401/403 = tout est interdit,
        # autre 4xx (pas de robots.txt) = rien n'est interdit.
        if exc.code not in (401, 403) and 400 <= exc.code < 500:
            return
        raise CollectError(f"robots.txt inaccessible ({exc.code}) : {robots_url}") from exc
    except urllib.error.URLError as exc:
        raise CollectError(f"robots.txt inaccessible ({exc.reason}) : {robots_url}") from exc
    if not robots_allows(robots_txt, url, user_agent):
        raise CollectError(f"robots.txt interdit la lecture de {url}")


def parse_feed(content: bytes, source: str) -> list[Item]:
    """Transforme le contenu d'un flux RSS ou Atom en items. Fonction pure, sans réseau."""
    feed = feedparser.parse(content)
    if not feed.entries and (feed.bozo or not feed.version):
        raise CollectError(f"{source} : le contenu reçu n'est pas un flux RSS ou Atom lisible")

    items = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        url = (entry.get("link") or "").strip()
        if not title or not url:
            continue  # sans titre ou sans lien, l'item est inutilisable
        items.append(
            Item(
                source=source,
                title=title,
                summary=(entry.get("summary") or "").strip(),
                url=url,
                published_at=_published_at(entry),
            )
        )
    return items


def _published_at(entry: feedparser.FeedParserDict) -> datetime | None:
    # feedparser donne déjà les dates en UTC (struct_time), quel que soit le fuseau du flux.
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed is None:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=UTC)


def collect(source: Source, user_agent: str, timeout: float) -> list[Item]:
    """Vérifie robots.txt, télécharge le flux de la source et le parse."""
    check_robots(source.acces, user_agent, timeout)
    try:
        content = http_get(source.acces, user_agent, timeout)
    except urllib.error.URLError as exc:
        raise CollectError(f"{source.nom} : lecture impossible de {source.acces} ({exc})") from exc
    return parse_feed(content, source.nom)


def write_json(items: list[Item], source: Source, directory: Path, collected_at: datetime) -> Path:
    """Écrit les items dans data/<source>-<horodatage UTC>.json et renvoie le chemin."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slugify(source.nom)}-{collected_at:%Y%m%dT%H%M%SZ}.json"
    payload = {
        "source": source.nom,
        "feed_url": source.acces,
        "collected_at": collected_at.isoformat(),
        "items": [item.to_dict() for item in items],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
