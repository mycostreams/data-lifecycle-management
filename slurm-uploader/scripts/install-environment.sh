#!/bin/bash

module purge
module load 2023
module load poetry/1.5.1-GCCcore-12.3.0

export POETRY_VIRTUALENVS_IN_PROJECT=true

cd $HOME/mycostreams/slurm-uploader

poetry install
