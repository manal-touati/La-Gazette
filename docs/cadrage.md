# La gazette — note de cadrage (TD 1)

## Équipe et rôles

| Rôle | Responsable |
|---|---|
| Collecte et sources (flux, `sources.csv`, conditions éditeurs) | _à compléter_ |
| Stockage et modèle de données (Postgres) | _à compléter_ |
| Nettoyage et contrôle qualité | _à compléter_ |
| Regroupement par thèmes | _à compléter_ |
| Livraison de l'édition | _à compléter_ |
| Ordonnancement, infra (Docker, Airflow) et supervision | _à compléter_ |

## Le besoin, avec nos mots

Chaque matin à 7 h, publier une « édition » qui montre de quoi parle la presse française : les grands thèmes des dernières 24 h, quels journaux (régionaux et nationaux) les traitent, et un lien vers chaque article. On ne produit pas d'articles : on lit des flux publics et on les range par thèmes.

## Périmètre

**Dans le périmètre** : collecte des flux RSS de 5 titres PQN et 6 titres PQR, stockage du brut, nettoyage (fraîcheur < 24 h, dédoublonnage, normalisation), regroupement automatique par thèmes, une édition HTML/Markdown par jour, supervision du pipeline, déploiement reproductible.

**Hors périmètre** : texte intégral des articles (scraping), résumés d'articles par LLM, front soigné, commentaires et profils, contournement d'un paywall ou d'une protection anti-robot.

## Contraintes

- Édition disponible à **7 h** (Europe/Paris), articles publiés depuis **moins de 24 h**.
- On ne garde que **titre, extrait, lien, date, source**. Le champ auteur présent dans certains flux n'est **pas** stocké (aucune donnée personnelle).
- On respecte `robots.txt` et les réserves TDM des éditeurs, avec un User-Agent identifié et aucun contournement.
- **Budget zéro** : nos machines, puis l'infrastructure fournie (TD 4 ou 6).

## Stack retenue

| Brique | Choix | Pourquoi |
|---|---|---|
| Langage | Python 3.12 | Écosystème (feedparser, pandas, sentence-transformers), compatible Airflow |
| Collecte | Flux RSS + `feedparser` | Stable, prévu pour être lu par des machines, contient déjà titre/extrait/lien/date |
| Ordonnancement | Apache Airflow (LocalExecutor) | Retries, relance manuelle, historique des runs : on sait dire si le pipeline a tourné |
| Stockage | PostgreSQL : schémas `raw` (JSONB), `staging`, `analytics`, `ops` | Une seule base, URL canonique `UNIQUE`, pipeline rejouable depuis le brut |
| Regroupement | Embeddings multilingues locaux (`sentence-transformers`) + HDBSCAN via BERTopic, thèmes nommés par mots-clés c-TF-IDF | Gratuit, tourne sur CPU, déterministe à paramètres fixés |
| Livraison | Page HTML + Markdown statiques (Jinja2), servies par nginx | Simple, archivable, sans front à maintenir |
| Supervision | UI Airflow + table `ops.runs` + contrôles par source + alerte en cas d'échec | Suffisant pour un pipeline quotidien |
| Infra as code | Docker Compose | Même stack sur nos PC et sur la VM fournie |

Schéma : [architecture.md](architecture.md). Détail de la veille : [veille.md](veille.md).

## Alternatives écartées

- **Scraping du texte intégral (trafilatura)** : hors sujet, paywalls, CGU et droit de fouille, maintenance fragile.
- **cron + script** : pas d'historique, de retries ni d'interface. On ne pourrait pas prouver que le pipeline a tourné.
- **MongoDB** : dédoublonnage et suivi des runs moins naturels qu'en SQL.
- **LLM pour nommer ou résumer les thèmes** : coût incompatible avec le budget zéro, résultats non déterministes, et le résumé par LLM est explicitement hors sujet. À revoir plus tard avec un modèle local, seulement si le reste est robuste.
- **Prometheus + Grafana** : surdimensionné à ce stade (envisageable après la mise en production).
- **Terraform + cloud managé** : coût et complexité. L'infrastructure nous sera fournie.
- **Sources écartées après vérification** (le 12/11/2026) : *La Voix du Nord* (403 Akamai pour les robots), *Le Télégramme* (403 Cloudflare), *Sud Ouest* (boucle de redirection, cookie exigé), *Les Échos* (503/403 sur toutes les adresses testées), *L'Humanité* (`robots.txt` interdit `*/feed`), *Le Parisien* (ni date ni extrait par article). On ne contourne aucune de ces protections.

## Constat qui structure l'architecture

Les flux ne gardent que les N derniers articles : **Ouest-France n'en garde que 10, soit moins d'une heure**. Une seule collecte à 6 h raterait presque tout. Il y a donc **deux traitements** : la collecte toutes les 30 min, qui accumule dans `raw`, et la production de l'édition chaque matin à partir de ce qui a été accumulé.

## Risques

| Risque | Parade |
|---|---|
| Un flux change d'URL, se vide ou nous bloque | Contrôle de volume par source, alerte si 0 article ou baisse anormale |
| PC éteints la nuit, donc trous dans la collecte | Mesurés dans `ops.runs` ; résolus par la VM fournie au TD 4 ou 6 |
| Réserve TDM (Le Figaro, Ouest-France) | Usage limité à titre, extrait et lien ; validation avec l'enseignant, demande d'accord, sinon remplacement (20 Minutes, Midi Libre) |
| Fuseaux horaires hétérogènes (GMT, +01:00) | Tout en UTC en base, Europe/Paris à l'affichage |
| Doublons (même dépêche AFP reprise partout) | URL canonique unique et quasi-doublons sur le titre |
| Thèmes peu lisibles (faible volume, quelques centaines d'articles par jour) | Paramètres fixés, relecture manuelle des premières éditions |
| Airflow lourd sur nos PC (~4 Go de RAM) | LocalExecutor, sans Celery ni Redis |

## Suite

- **TD 2 (socle)** : dépôt, Docker Compose (Postgres + Airflow), schémas SQL, squelette de DAG.
- **TD 3 (collecte)** : DAG `collecte_flux`, une tâche par source lue depuis `sources.csv`, écriture dans `raw.items`.
