"""Tests de sources.csv : le fichier du dépôt doit rester lisible et conforme au cadrage."""

from pathlib import Path

import pytest

from gazette.sources import find_source, load_sources

SOURCES_CSV = Path(__file__).parents[1] / "sources.csv"


@pytest.fixture
def sources():
    return load_sources(SOURCES_CSV)


def test_sources_csv_conforme_au_cadrage(sources):
    types = [source.type for source in sources]
    assert set(types) == {"PQN", "PQR"}
    assert types.count("PQN") >= 4 and types.count("PQR") >= 4  # TD 1 : au moins 4 de chaque
    assert len({source.nom for source in sources}) == len(sources)  # pas de doublon
    assert all(source.acces.startswith("https://") for source in sources)


def test_find_source_ignore_la_casse(sources):
    assert find_source(sources, "la croix").acces == "https://www.la-croix.com/feeds/rss/site.xml"


def test_find_source_inconnue(sources):
    with pytest.raises(ValueError, match="Sources disponibles"):
        find_source(sources, "Le Canard")
