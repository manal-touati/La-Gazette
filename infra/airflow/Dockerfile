# Image Airflow de La gazette : Airflow officiel + dépendances du pipeline.
# Le code (dags/, src/) n'est pas copié : il est monté par docker-compose.yml.
# L'image de l'application, publiée par la CI, est le Dockerfile à la racine.
FROM apache/airflow:3.3.2-python3.12

# Dépendances déclarées dans pyproject.toml (dependencies + extra "dev" pour pytest).
# apache-airflow est épinglé pour que pip ne le mette pas à jour au passage.
# L'extra "themes" (torch CPU, BERTopic) sera ajouté au TD du regroupement par thèmes.
COPY pyproject.toml /tmp/pyproject.toml
RUN python -c "import tomllib; p = tomllib.load(open('/tmp/pyproject.toml', 'rb'))['project']; print('\n'.join(p['dependencies'] + p['optional-dependencies']['dev']))" \
        > /tmp/requirements.txt \
    && pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/requirements.txt

# Point de montage du volume des éditions, créé avec l'utilisateur airflow comme propriétaire.
RUN mkdir -p /opt/airflow/editions
