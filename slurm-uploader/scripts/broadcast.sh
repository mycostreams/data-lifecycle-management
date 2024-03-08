#!/bin/bash
#
#SBATCH --partition=staging
#SBATCH --export=CONNECTION_URL
#
# Broacast the result of a archiving job via a message broker

module purge
module load 2023
module load poetry/1.5.1-GCCcore-12.3.0

PARENT_JOB_ID=${1}

cd $HOME/pycode/mycostreams/slurm-uploader
poetry run cli publish $PARENT_JOB_ID

echo "$PARENT_JOB_ID completed"
