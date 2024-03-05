#!/bin/bash

DATE_STR=${1}

cd $(dirname $0)

ARCHIVE_JOB_ID=$(sbatch --parsable "./archive.sh" -d "$DATE_STR")

sbatch --dependency=afterok:${ARCHIVE_JOB_ID} "./propagate-result.sh" "$SLURM_JOB_ID"
