"""Tests de la collecte, sur un extrait réel du flux de La Croix (enregistré le 12/11/2026)."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from gazette.collect import CollectError, parse_feed, robots_allows, slugify, write_json
from gazette.sources import Source

FIXTURE = Path(__file__).parent / "fixtures" / "lacroix_site.xml"
UA = "LaGazette/0.1 (projet etudiant)"


@pytest.fixture
def items():
    return parse_feed(FIXTURE.read_bytes(), "La Croix")


def test_lit_tous_les_items_du_flux(items):
    assert len(items) == 3
    first = items[0]
    assert first.source == "La Croix"
    assert first.title.startswith("Guerre en Ukraine")
    assert first.summary.startswith("Les émissaires américains")
    assert first.url == (
        "https://www.la-croix.com/international/"
        "ukraine-russie-jour-1723-point-conflit-ukrainien-poutine-aujourdhui-20261112"
    )


def test_dates_converties_en_utc(items):
    # Dans le flux : <pubDate>Thu, 12 Nov 2026 10:27:38 +0100</pubDate>
    assert items[0].published_at == datetime(2026, 11, 12, 9, 27, 38, tzinfo=UTC)


def test_auteur_jamais_conserve(items):
    # Le flux contient <dc:creator>Marianne Meunier</dc:creator> : ce nom ne doit sortir nulle part.
    assert "Marianne Meunier" in FIXTURE.read_text(encoding="utf-8")
    for item in items:
        data = item.to_dict()
        assert set(data) == {"source", "title", "summary", "url", "published_at"}
        assert "Marianne Meunier" not in json.dumps(data, ensure_ascii=False)


def test_item_sans_lien_ou_sans_date():
    xml = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Test</title>
        <item><title>Sans lien</title></item>
        <item><title>Sans date</title><link>https://exemple.fr/a</link></item>
    </channel></rss>"""
    items = parse_feed(xml, "Test")
    assert [item.title for item in items] == ["Sans date"]
    assert items[0].published_at is None


@pytest.mark.parametrize("content", [b"<html><body>Access denied</body></html>", b"\x00\x01"])
def test_contenu_qui_n_est_pas_un_flux(content):
    with pytest.raises(CollectError):
        parse_feed(content, "Test")


def test_robots_txt_autorise_le_flux():
    robots = "User-agent: *\nDisallow: /recherche/\nDisallow: /Archives/\n"
    assert robots_allows(robots, "https://www.la-croix.com/feeds/rss/site.xml", UA)


def test_robots_txt_interdit_le_flux():
    robots = "User-agent: *\nDisallow: /\n"
    assert not robots_allows(robots, "https://exemple.fr/rss.xml", UA)


def test_write_json(tmp_path, items):
    source = Source("La Croix", "PQN", "National", "https://exemple.fr/rss.xml", "", "")
    path = write_json(items, source, tmp_path, datetime(2026, 11, 12, 9, 30, tzinfo=UTC))

    assert path.name == "la-croix-20261112T093000Z.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["source"] == "La Croix"
    assert data["collected_at"] == "2026-11-12T09:30:00+00:00"
    assert data["items"][0]["published_at"] == "2026-11-12T09:27:38+00:00"
    assert "émissaires" in path.read_text(encoding="utf-8")  # accents écrits tels quels


def test_slugify():
    assert slugify("Dernières Nouvelles d'Alsace") == "dernieres-nouvelles-d-alsace"
