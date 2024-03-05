#!/bin/bash

module purge
module load 2023
module load poetry/1.5.1-GCCcore-12.3.0

cd $HOME/slurm-uploader/

poetry install
