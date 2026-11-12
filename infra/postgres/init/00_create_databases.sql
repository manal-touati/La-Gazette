-- Exécuté une seule fois par l'image postgres, au premier démarrage (volume
-- pgdata vide), connecté en tant que "gazette" sur la base "gazette".
--
-- La base "gazette" (données du pipeline) est créée par l'image elle-même
-- (POSTGRES_DB). On ajoute ici la base des métadonnées d'Airflow, avec son
-- propre rôle, pour que les tables d'Airflow et celles du pipeline restent
-- séparées.

\getenv airflow_db_password AIRFLOW_DB_PASSWORD

CREATE ROLE airflow LOGIN PASSWORD :'airflow_db_password';
CREATE DATABASE airflow OWNER airflow;
