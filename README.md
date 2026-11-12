# La gazette

Chaque matin à 7 h, une édition qui montre de quoi parle la presse française : les grands thèmes des dernières 24 h, les journaux qui les traitent et un lien vers chaque article. On lit les flux RSS publics des éditeurs, on ne stocke que titre, extrait, lien, date et source.

Cadrage : [docs/cadrage.md](docs/cadrage.md) · Architecture : [docs/architecture.md](docs/architecture.md) · CI/CD : [docs/ci-cd.md](docs/ci-cd.md)

## Lancer

Prérequis : Docker (Desktop ou Engine + Compose v2) avec 4 Go de RAM, et Git. Sous Windows, lancez les commandes dans **Git Bash** (installé avec Git).

```bash
git clone https://github.com/manal-touati/La-Gazette.git && cd La-Gazette
bin/dev
```

Aucun fichier à remplir en dev. Le premier lancement télécharge Airflow (~2,5 Go) : comptez quelques minutes.

| Service | Adresse | Rôle |
|---|---|---|
| Airflow | http://localhost:8080 (admin / admin) | Ordonnancement : DAGs, runs, logs |
| Éditions | http://localhost:8000 | Les éditions publiées, servies par nginx |
| PostgreSQL | `localhost:5432`, base et utilisateur `gazette` | Stockage du pipeline |
| app | `docker compose logs app` | L'application : lit une source (La Croix) et écrit ses items en JSON |

Autres commandes : `bin/dev stop` (arrêter), `bin/dev logs` (suivre les logs), `bin/dev reset` (arrêter et **effacer** les données). Un port déjà pris ? Copiez `.env.example` en `.env` et changez `AIRFLOW_PORT`, `EDITIONS_PORT` ou `POSTGRES_PORT`.

Lire une autre source de [sources.csv](sources.csv) :

```bash
docker compose run --rm app collect "Nice-Matin"
```

## Tester

```bash
bin/test               # ruff (lint + format) puis pytest, dans un conteneur, comme la CI
bin/test -k robots     # seulement pytest, avec ces arguments
```

Sans Docker, dans un environnement Python 3.12 : `pip install -e ".[dev]"`, puis `ruff check .`, `ruff format .` et `pytest`.

## Contribuer

Une branche par sujet, une pull request vers `main`, la CI verte et une relecture avant de fusionner : tout est dans [CONTRIBUTING.md](CONTRIBUTING.md).

## Organisation du dépôt

```
src/gazette/         le code du pipeline (collecte, nettoyage, thèmes, édition)
tests/               les tests, et tests/fixtures/ : des extraits réels de flux enregistrés
dags/                les DAGs Airflow (TD 3)
infra/               l'image Airflow, les scripts d'init Postgres, la config nginx
docs/                cadrage, veille, architecture, stratégie CI/CD
bin/dev, bin/test    lancer et tester
Dockerfile           l'image de l'application, publiée sur ghcr.io par la CI
docker-compose.yml   l'environnement complet (app, Postgres, Airflow, nginx)
sources.csv          les flux suivis, comment on les lit, leurs conditions
```

Les scripts de `infra/postgres/init/` ne s'exécutent qu'au premier démarrage, sur une base vide : après les avoir modifiés, `bin/dev reset` puis `bin/dev`.
