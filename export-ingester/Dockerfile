# The builder image, used to build the virtual environment
FROM python:3.12-bullseye as builder

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/opt/.cache 

ENV PATH=$POETRY_HOME/bin:$PATH

RUN curl -sSL https://install.python-poetry.org | python3 - 

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --with dev && rm -rf $POETRY_CACHE_DIR


# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12-slim-bullseye as runtime

ENV VENV_PATH=/app/.venv
ENV PATH=$VENV_PATH/bin:$PATH

WORKDIR /app

COPY --from=builder ${VENV_PATH} ${VENV_PATH}

COPY ./export_ingester /app/export_ingester
