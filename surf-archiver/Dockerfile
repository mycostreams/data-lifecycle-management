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

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --with remote && rm -rf $POETRY_CACHE_DIR

COPY ./surf_archiver /app/surf_archiver
RUN poetry install --only-root


# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12-slim-bullseye as runtime

WORKDIR /app

ENV VENV_PATH=/app/.venv
ENV PATH=$VENV_PATH/bin:$PATH

COPY --from=builder ${VENV_PATH} ${VENV_PATH}

COPY ./surf_archiver /app/surf_archiver
COPY ./scripts/prestart.sh /app/scripts/prestart.sh


# SSH server with cli tool installed
FROM runtime as ssh-server

RUN apt-get update && \
    apt-get install -y openssh-server && \
    rm -rf /var/lib/apt/lists/*

RUN sed -i 's/#PermitUserEnvironment no/PermitUserEnvironment yes/' /etc/ssh/sshd_config
RUN mkdir /var/run/sshd

COPY ./scripts/entrypoint.sh /app/scripts/entrypoint.sh

EXPOSE 22

ENTRYPOINT [ "/app/scripts/entrypoint.sh" ]
