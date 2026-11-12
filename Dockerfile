# Image de l'application La gazette (commande `gazette`), publiée par la CI sur ghcr.io.
#   build   : installe le paquet et ses dépendances dans un venv
#   test    : lint + tests (bin/test), jamais publiée
#   runtime : image finale, petite, sans outils de build, utilisateur non root

FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/opt/venv/bin:$PATH
RUN python -m venv /opt/venv
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .


FROM build AS test
RUN pip install ".[dev]"
COPY sources.csv ./
COPY tests ./tests
CMD ["sh", "-c", "ruff check . && ruff format --check . && pytest"]


FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    GAZETTE_SOURCES_FILE=/app/sources.csv \
    GAZETTE_DATA_DIR=/data
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin gazette \
    && mkdir /data \
    && chown gazette /data
COPY --from=build /opt/venv /opt/venv
COPY sources.csv /app/sources.csv
USER gazette
WORKDIR /data
ENTRYPOINT ["gazette"]
CMD ["--help"]
