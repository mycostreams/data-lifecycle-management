#!/bin/bash
#
#SBATCH --partition=staging
#SBATCH --export=CONNECTION_URL
#
# Run the full archiving routine.
#  Step 1: Retrieve data from cloud and archive
#  Step 2: Broadcast the outcome via message broker

DATE_STR=${1}

cd $(dirname $0)

# Step 1: Archive
ARCHIVE_JOB_ID=$(sbatch \
    --parsable \
    "./archive.sh" -d "$DATE_STR" \
)
echo "Archiving job: $ARCHIVE_JOB_ID"

# Step 2: Braodcast
BROADCAST_JOB_ID=$(sbatch \
    --parsable \
    --dependency=afterok:$ARCHIVE_JOB_ID \
    "./broadcast.sh" "$SLURM_JOB_ID" \
)
echo "Broadcasting job: $BROADCAST_JOB_ID"
