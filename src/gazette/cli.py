"""Ligne de commande : `gazette collect "La Croix"`."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from gazette import config
from gazette.collect import CollectError, collect, write_json
from gazette.sources import find_source, load_sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gazette", description="La gazette, la presse du matin.")
    commands = parser.add_subparsers(dest="command", required=True)

    collect_cmd = commands.add_parser("collect", help="lit le flux d'une source, écrit du JSON")
    collect_cmd.add_argument("source", help='nom de la source dans sources.csv, ex. "La Croix"')
    collect_cmd.add_argument(
        "--sources", type=Path, default=config.SOURCES_FILE, help="fichier des sources"
    )
    collect_cmd.add_argument(
        "--out", type=Path, default=config.DATA_DIR, help="dossier où écrire le JSON"
    )

    args = parser.parse_args(argv)
    try:
        source = find_source(load_sources(args.sources), args.source)
        items = collect(source, config.USER_AGENT, config.HTTP_TIMEOUT)
    except (OSError, ValueError, CollectError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    path = write_json(items, source, args.out, datetime.now(UTC))
    print(f"{source.nom} : {len(items)} items écrits dans {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
