"""Réglages lus dans l'environnement, avec des valeurs par défaut pour le dev local."""

import os
from pathlib import Path

SOURCES_FILE = Path(os.environ.get("GAZETTE_SOURCES_FILE", "sources.csv"))
DATA_DIR = Path(os.environ.get("GAZETTE_DATA_DIR", "data"))

# User-Agent identifié, envoyé à chaque requête (docs/cadrage.md, contraintes).
USER_AGENT = os.environ.get("GAZETTE_USER_AGENT", "LaGazette/0.1 (projet etudiant)")
HTTP_TIMEOUT = 30  # secondes
