#!/bin/bash

module purge
module load 2023
module load poetry/1.5.1-GCCcore-12.3.0

export POETRY_VIRTUALENVS_IN_PROJECT=true
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

cd $HOME/mycostreams/slurm-uploader

poetry install
