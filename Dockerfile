FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.4.1 --no-cache
RUN poetry config virtualenvs.create false

COPY [ "poetry.toml", "poetry.lock", "pyproject.toml", "./" ]

# We don't want the tests
COPY src/az ./src/az

RUN poetry install --no-dev

ARG APP_VERSION
ENV APP_VERSION=$APP_VERSION

ENTRYPOINT [ "python", "-m", "az" ]
CMD [ "handle-updates" ]
