#!/bin/bash
#SBATCH --partition=staging
#SBATCH --export=CONNECTION_URL
#
# Run the full archiving routine.
#  Step 1: Retrieve data from cloud and archive
#  Step 2: Broadcast the outcome via message broker

DATE_STR=${1}
JOB_ID=$(uuidgen)

OUTPUT_DIR=/scratch-local/mycostreams/$JOB_ID
mkdir -p $OUTPUT_DIR

cd $HOME/pycode/mycostreams/slurm-uploader

# Step 1: Archive
ARCHIVE_JOB_ID=$(sbatch \
    --parsable \
    --output "$OUTPUT_DIR/slurm-%A.out" \
    "./scripts/archive.sh" -d "$DATE_STR" \
)


# Step 2: Broadcast
sbatch \
    --parsable \
    --output "$OUTPUT_DIR/slurm-%A.out" \
    --dependency=afterok:$ARCHIVE_JOB_ID \
    "./scripts/broadcast.sh" "$JOB_ID" \

echo $JOB_ID
