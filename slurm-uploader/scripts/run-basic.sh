#!/bin/bash
#
#SBATCH --partition=staging
#SBATCH --export=CONNECTION_URL
#
# Broadcast the job id of the parent

DATE_STR=${1}

cd $(dirname $0)

# Step 2: Braodcast
BROADCAST_JOB_ID=$(sbatch \
    --parsable \
    "./broadcast.sh" "$SLURM_JOB_ID" \
)

echo "Broadcasting job: $BROADCAST_JOB_ID"
