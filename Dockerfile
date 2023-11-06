FROM ghcr.io/blindfoldedsurgery/poetry:1.0.0-pipx-3.11-bookworm

COPY [ "poetry.toml", "poetry.lock", "pyproject.toml", "./" ]

RUN poetry install --no-interaction --ansi --only=main --no-root

# We don't want the tests
COPY src/az ./src/az

RUN poetry install --no-interaction --ansi --only-root

ARG APP_VERSION
ENV APP_VERSION=$APP_VERSION

CMD [ "python", "-m", "az", "handle-updates" ]
