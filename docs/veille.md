# La gazette — veille technologique (TD 1)

Six sujets, deux options chacun, leurs limites et notre recommandation.

## 1. Récupérer la presse

| Option | Limite |
|---|---|
| **A. Flux RSS + `feedparser`** (titre, extrait, URL, date) | Pas de texte complet ; flux parfois supprimés, modifiés ou bloqués aux robots |
| B. Scraping du texte complet (`trafilatura`) | Paywall, CGU et droit de fouille (TDM), maintenance fragile, hors sujet |

**Reco : A.** Stable, légal, suffisant pour titre + extrait.
**Pièges vérifiés le 12/11/2026** : flux très courts (Ouest-France : 10 articles, soit moins d'une heure, d'où une collecte fréquente), flux sans date (Le Parisien), articles très anciens mélangés aux récents (La Dépêche, 20 Minutes), fuseaux horaires hétérogènes, champ auteur à ne pas stocker, réserves TDM (`/.well-known/tdmrep.json` chez Le Figaro et Ouest-France), protections anti-robot (La Voix du Nord, Le Télégramme), `robots.txt` interdisant les flux (L'Humanité).

## 2. Faire tourner chaque matin

| Option | Limite |
|---|---|
| **A. Airflow** (DAG, dans Docker) | Lourd pour un petit pipeline (~4 Go de RAM) |
| B. cron + script Python | Pas d'historique des runs, ni de retries, ni d'interface |

**Reco : A** (LocalExecutor). Une tâche par source, retries, relance manuelle, historique : on peut prouver que le pipeline a tourné.

## 3. Stocker (brut, propre)

| Option | Limite |
|---|---|
| **A. PostgreSQL** (`raw` en JSONB, `staging`/`analytics` en tables, `ops.runs`) | Pas fait pour de très gros volumes (ce n'est pas notre cas) |
| B. MongoDB | Jointures et dédoublonnage plus lourds, moins adapté au suivi des runs |

**Reco : A.** Une seule base, URL canonique `UNIQUE`, pipeline rejouable depuis le brut.

## 4. Regrouper des textes par thèmes

| Option | Limite |
|---|---|
| **A. Embeddings + clustering** (BERTopic, k-means, HDBSCAN) | Thèmes à nommer, paramètres à régler |
| B. LLM direct (classification ou regroupement par prompt) | Coût, résultats non déterministes |

**Reco : A seul**, avec un modèle d'embeddings multilingue local et des thèmes nommés par mots-clés (c-TF-IDF de BERTopic).
L'hybride « LLM pour nommer et résumer les thèmes » est écarté pour l'instant : le budget est nul, le résumé par LLM est hors sujet, et le résultat n'est pas reproductible. On pourra le revoir avec un modèle local si le reste est robuste.

## 5. Surveiller le pipeline

| Option | Limite |
|---|---|
| **A. Airflow natif** (UI, alerte en cas d'échec) + table `ops.runs` | Pas de métriques fines |
| B. Prometheus + Grafana (+ Loki) | Surdimensionné, plus de conteneurs à gérer |

**Reco : A**, avec des contrôles qualité par source (nombre d'articles, fraîcheur). B éventuellement après la mise en production.

## 6. Décrire l'infrastructure en code

| Option | Limite |
|---|---|
| **A. Docker Compose** (Airflow, Postgres, nginx, sur nos PC puis sur une VM) | Peu scalable, pas de haute disponibilité |
| B. Terraform + cloud managé (VM/Kubernetes, Postgres managé) | Coût et complexité |

**Reco : A.** L'infrastructure de production nous sera fournie. B serait pertinent pour un hébergement cloud reproductible, hors budget ici.
