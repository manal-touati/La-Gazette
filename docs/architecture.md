# La gazette — architecture

```mermaid
flowchart LR
    SRC["Flux RSS des éditeurs<br/>5 PQN + 6 PQR<br/>(sources.csv)"]

    subgraph HOST["Docker Compose : nos PC, puis VM fournie (TD 4/6)"]
        direction LR
        subgraph AIRFLOW["Airflow (scheduler + UI)"]
            C["1. Collecte<br/>feedparser<br/>DAG collecte_flux, toutes les 30 min"]
            N["3. Nettoyage + contrôle qualité<br/>DAG edition_du_jour, 6 h 00"]
            T["4. Regroupement par thèmes<br/>embeddings + HDBSCAN"]
            L["5. Livraison<br/>rendu Jinja2"]
        end
        subgraph PG["PostgreSQL"]
            RAW[("2. Stockage brut<br/>raw.items (JSONB)")]
            STG[("staging.articles")]
            AN[("analytics.themes<br/>analytics.theme_articles")]
            OPS[("ops.runs<br/>ops.source_checks")]
        end
        WEB["nginx<br/>editions/AAAA-MM-JJ.html"]
    end

    SUP["6. Supervision<br/>UI Airflow, ops.runs, alertes"]
    LECT["Lecteurs, 7 h 00"]
    EQ["Équipe"]

    SRC -- "XML RSS via HTTP<br/>User-Agent identifié" --> C
    C -- "1 ligne par item<br/>JSON brut + source + heure de collecte" --> RAW
    RAW --> N
    N -- "titre, extrait, URL canonique, date UTC<br/>moins de 24 h, dédoublonné, sans auteur" --> STG
    STG --> T
    T -- "thèmes, mots-clés,<br/>articles rattachés" --> AN
    AN --> L
    L -- "HTML + Markdown" --> WEB
    WEB --> LECT

    C -. "statut, nb d'items par source" .-> OPS
    N -. "volumes, rejets, fraîcheur" .-> OPS
    T -. "nb de thèmes, durée" .-> OPS
    L -. "édition publiée, heure" .-> OPS
    OPS --> SUP
    AIRFLOW -. "échecs, retries" .-> SUP
    SUP -. "alerte si échec ou source vide" .-> EQ
```

## Ce qui circule entre les boîtes

| De → vers | Contenu | Où |
|---|---|---|
| Éditeurs → 1. Collecte | XML RSS 2.0 | HTTP, User-Agent identifié, `robots.txt` respecté |
| 1 → 2. Brut | L'item tel que reçu (JSONB), source, `collected_at` | `raw.items`, insertion seule, rejouable |
| 2 → 3. Nettoyage | Items collectés depuis 24 h | lecture SQL |
| 3 → 4. Regroupement | `source, titre, extrait, url_canonique, published_at (UTC)`, sans auteur | `staging.articles`, `url_canonique UNIQUE` |
| 4 → 5. Livraison | Thèmes (libellé par mots-clés, taille, sources) et articles rattachés | `analytics.*` |
| 5 → lecteurs | Édition du jour : thèmes, titres, liens | `editions/AAAA-MM-JJ.html` et `.md` |
| Toutes → 6. Supervision | Statut, durée, volumes par source, rejets | `ops.*` et UI Airflow |

## Où ça tourne et quand

| Traitement | Déclencheur | Pourquoi |
|---|---|---|
| `collecte_flux` | toutes les 30 min | Certains flux ne gardent que la dernière heure (Ouest-France : 10 articles) |
| `edition_du_jour` | 6 h 00 Europe/Paris, retries jusqu'à 6 h 45 | Laisser une marge avant la sortie de 7 h |

Tous les conteneurs (Postgres, Airflow, nginx) sont décrits dans `docker-compose.yml` (TD 2). Ils tournent sur nos PC, puis sur la VM fournie pour la mise en production.
