import json
from datetime import UTC, datetime, timedelta

import pytest

from gazette.models import Item
from gazette.transform_news import (
    RULE_EXCLUDED_SECTION,
    RULE_FUTURE_DATE,
    RULE_REQUIRED_FIELDS,
    read_raw_json,
    transform_items,
    transform_items_with_report,
)

NOW = datetime(2026, 11, 12, 12, tzinfo=UTC)


def test_read_raw_json_retrouve_les_items_de_la_source(tmp_path):
    path = tmp_path / "la-croix.json"
    path.write_text(
        json.dumps(
            {
                "source": "La Croix",
                "items": [
                    {
                        "source": "La Croix",
                        "title": "Titre",
                        "summary": "Résumé",
                        "url": "https://exemple.fr/article",
                        "published_at": "2026-11-12T11:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    items = read_raw_json(path, "La Croix")

    assert items == [
        Item(
            "La Croix",
            "Titre",
            "Résumé",
            "https://exemple.fr/article",
            datetime(2026, 11, 12, 11, tzinfo=UTC),
        )
    ]


def test_read_raw_json_refuse_une_autre_source(tmp_path):
    path = tmp_path / "la-croix.json"
    path.write_text(json.dumps({"source": "La Croix", "items": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="pas 'Le Monde'"):
        read_raw_json(path, "Le Monde")


def test_transform_items_nettoie_filtre_et_dedoublonne():
    items = [
        Item(
            "La Croix",
            "  Titre\narticle ",
            " résumé  avec   espaces ",
            "https://exemple.fr/a#section",
            NOW - timedelta(hours=1),
        ),
        Item(
            "La Croix",
            "Doublon",
            "Résumé",
            "https://exemple.fr/a",
            NOW - timedelta(hours=2),
        ),
        Item(
            "La Croix",
            "Ancien",
            "Résumé",
            "https://exemple.fr/b",
            NOW - timedelta(hours=25),
        ),
    ]

    result = transform_items(items, now=NOW)

    assert len(result) == 1
    assert result[0].title == "Titre article"
    assert result[0].summary == "résumé avec espaces"
    assert result[0].url == "https://exemple.fr/a"


@pytest.mark.parametrize(
    "item",
    [
        Item("La Croix", "", "Résumé", "https://exemple.fr/a", NOW),
        Item("La Croix", "Titre", "", "https://exemple.fr/b", NOW),
        Item("La Croix", "Horoscope du jour", "Résumé", "https://exemple.fr/c", NOW),
        Item("La Croix", "Programme TV", "Résumé", "https://exemple.fr/d", NOW),
        Item("La Croix", "Jeu concours", "Résumé", "https://exemple.fr/e", NOW),
        Item("La Croix", "Contenu partenaire", "Résumé", "https://exemple.fr/f", NOW),
        Item("La Croix", "Actualité Ã©conomique", "Résumé", "https://exemple.fr/g", NOW),
        Item("La Croix", "Titre", "Résumé", "https://exemple.fr/h", NOW + timedelta(minutes=1)),
        Item("La Croix", "Titre", "Résumé", "https://exemple.fr/i", NOW - timedelta(hours=25)),
        Item("La Croix", "Titre", "Résumé", "not-a-url", NOW),
    ],
)
def test_transform_items_rejette_les_articles_invalides(item):
    assert transform_items([item], now=NOW) == []


def test_transform_items_rejette_les_titres_approchants():
    items = [
        Item("La Croix", "Guerre en Ukraine ce matin", "Résumé", "https://exemple.fr/a", NOW),
        Item(
            "La Croix",
            "Guerre en Ukraine ce matin à Kiev",
            "Résumé",
            "https://exemple.fr/b",
            NOW,
        ),
    ]

    result = transform_items(items, now=NOW)

    assert [item.url for item in result] == ["https://exemple.fr/a"]


def test_transform_items_rejette_les_urls_dupliquees():
    items = [
        Item("La Croix", "Premier titre", "Résumé", "https://exemple.fr/a", NOW),
        Item("La Croix", "Deuxième titre", "Résumé", "https://exemple.fr/a#section", NOW),
    ]

    result = transform_items(items, now=NOW)

    assert [item.title for item in result] == ["Premier titre"]


def test_transform_items_nettoie_le_html():
    item = Item(
        "La Croix",
        "<strong>Titre</strong>",
        "<p>Résumé &amp; détail</p>",
        "https://exemple.fr/a",
        NOW,
    )

    result = transform_items([item], now=NOW)

    assert result[0].title == "Titre"
    assert result[0].summary == "Résumé & détail"


def test_transform_items_with_report_compte_les_rejets_par_regle():
    items = [
        Item("La Croix", "", "Résumé", "https://exemple.fr/a", NOW),
        Item("La Croix", "Horoscope", "Résumé", "https://exemple.fr/b", NOW),
        Item("La Croix", "Titre", "Résumé", "https://exemple.fr/c", NOW + timedelta(minutes=1)),
    ]

    result, report = transform_items_with_report(items, now=NOW)

    assert result == []
    assert report.input_count == 3
    assert report.kept_count == 0
    assert report.rejected_count == 3
    assert report.rejected_by_rule[RULE_REQUIRED_FIELDS] == 1
    assert report.rejected_by_rule[RULE_EXCLUDED_SECTION] == 1
    assert report.rejected_by_rule[RULE_FUTURE_DATE] == 1
