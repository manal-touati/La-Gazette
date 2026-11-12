"""Lecture de sources.csv : les flux suivis, comment on les lit, leurs conditions."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    nom: str
    type: str  # PQN ou PQR
    region: str
    acces: str  # adresse du flux RSS
    conditions: str
    notes: str


def load_sources(path: Path) -> list[Source]:
    with path.open(encoding="utf-8", newline="") as f:
        return [Source(**row) for row in csv.DictReader(f)]


def find_source(sources: list[Source], nom: str) -> Source:
    """Retrouve une source par son nom, sans tenir compte de la casse."""
    for source in sources:
        if source.nom.casefold() == nom.casefold():
            return source
    noms = ", ".join(s.nom for s in sources)
    raise ValueError(f"source inconnue : {nom!r}. Sources disponibles : {noms}")
