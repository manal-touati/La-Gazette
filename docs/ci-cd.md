# La gazette : stratégie CI/CD

1. **Branches** : `main` est toujours déployable et protégée ; une branche par sujet, fusionnée par pull request après relecture ([CONTRIBUTING.md](../CONTRIBUTING.md)).
2. **Déclencheurs** : la CI ([.github/workflows/ci.yml](../.github/workflows/ci.yml), GitHub Actions) tourne sur chaque pull request et sur chaque push sur `main`.
3. **Étapes** : `lint` (`ruff check`, `ruff format --check`) → `tests` (`pytest`) → `image` (build du [Dockerfile](../Dockerfile), étape `runtime`). Chaque job ne démarre que si le précédent est vert.
4. **Publication** : sur `main` seulement, l'image est poussée sur `ghcr.io/manal-touati/la-gazette` avec le tag `AAAAMMJJHHMMSS-sha` (date UTC du build et 7 premiers caractères du commit), plus `latest`. Une pull request construit l'image sans la publier.
5. **Garde-fou** : la règle de protection de `main` exige les jobs `lint`, `tests` et `image` verts et une approbation. Une CI rouge bloque donc le merge.
6. **En local** : `bin/test` lance les mêmes contrôles dans un conteneur (étape `test` du Dockerfile), sans rien installer d'autre que Docker.
7. **L'image publiée** est petite (`python:3.12-slim`, environ 200 Mo), sans outils de build, et tourne avec un utilisateur non root.
8. **Hors périmètre pour l'instant** : pas de déploiement automatique (TD 7), pas de matrice de versions, pas de cache. L'image Airflow (`infra/airflow/`) est construite par `bin/dev`, pas par la CI.
9. **Réglages GitHub** faits une fois à la main, décrits ici : Settings → Rules → protection de `main` (checks `lint`, `tests` et `image` requis, 1 approbation, pas de push direct) ; après le premier push, rendre le paquet ghcr public (Package settings → Change visibility).
10. **Preuve qu'une CI rouge bloque** : une PR avec un test volontairement cassé doit afficher `tests` en échec et un bouton de merge désactivé.
