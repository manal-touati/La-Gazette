# Contribuer à La gazette

## Règles de base

- `main` est toujours déployable : on n'y pousse jamais directement, tout passe par une pull request.
- Rien de ce qui tourne n'est installé ni cliqué à la main sans être décrit dans le dépôt (Compose, CI, docs).
- Aucun secret dans le dépôt : `.env` reste sur votre machine (modèle : `.env.example`).
- Le cadrage s'applique au code : on ne garde que titre, extrait, lien, date et source ; jamais d'auteur ; on respecte `robots.txt` et les conditions des éditeurs.

## Branches

Une branche par sujet, créée depuis `main` à jour, en minuscules avec des tirets :

| Préfixe | Pour | Exemple |
|---|---|---|
| `feat/` | une fonctionnalité | `feat/collecte-nice-matin` |
| `fix/` | une correction | `fix/dates-sans-fuseau` |
| `docs/` | la documentation | `docs/cadrage-roles` |
| `ci/` | la CI, Docker, l'infra | `ci/push-ghcr` |
| `test/` | des tests seuls | `test/fixture-ouest-france` |

## Commits

Format [Conventional Commits](https://www.conventionalcommits.org/fr/), en français, à l'impératif :

```
type(portée): ce que fait le commit
```

Types : `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `build`, `chore`. Exemples : `feat(collecte): lire le flux de La Croix`, `fix(collecte): convertir les dates en UTC`. Un commit = un changement cohérent, et les tests passent.

## Avant d'ouvrir une pull request

```bash
bin/test
```

Si `ruff format --check` échoue, formatez avec `ruff format .` (dans un environnement où `pip install -e ".[dev]"` a été fait).

## Pull request et relecture

1. La PR vise `main` et dit en trois lignes : quoi, pourquoi, comment tester.
2. Il faut **la CI verte et une approbation** d'un autre membre de l'équipe : la protection de `main` bloque le merge sinon.
3. La relecture vérifie que la PR fait ce qu'elle annonce, que les tests couvrent le changement et que rien ne contredit le cadrage.
4. **Qui merge** : l'auteur·e de la PR, une fois l'approbation et la CI verte obtenues, en « Squash and merge ». La branche est ensuite supprimée.

## Ajouter ou modifier une source

Une ligne dans `sources.csv` (`nom,type,region,acces,conditions,notes`). Avant : vérifier à la main `robots.txt`, `/.well-known/tdmrep.json`, la balise `<copyright>` du flux et les en-têtes HTTP (`curl -I`). Notez ce que vous avez vu dans `conditions` et `notes`. Le test `tests/test_sources.py` vérifie que le fichier reste conforme au cadrage.
