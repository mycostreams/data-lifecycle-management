
FROM debian:bookworm-slim as fiji-builder

RUN apt-get update && apt-get install -y \
        wget \
        unzip \
    && rm -rf /var/lib/apt/

# Retrieve ImageJ and source code
WORKDIR /opt/fiji

RUN wget https://downloads.imagej.net/fiji/latest/fiji-nojre.zip \
    && unzip fiji-nojre.zip \
    && rm fiji-nojre.zip

# Micromamba-docker @ https://github.com/mamba-org/micromamba-docker
FROM mambaorg/micromamba:1.5.7-bookworm-slim

ARG MAMBA_DOCKERFILE_ACTIVATE=1

USER root

# Add fiji
COPY --from=fiji-builder /opt/fiji /opt/fiji
ENV FIJI_HOME /opt/fiji/Fiji.app


# Install python + java
RUN micromamba install -y -n base -c conda-forge \
        python=3.10 && \
        openjdk=11 && \
        pip \
    micromamba clean --all --yes


# Install the app
WORKDIR /app

COPY pyproject.toml requirements.txt /app/

RUN pip install -r requirements.txt
