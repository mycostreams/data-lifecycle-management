#!/bin/bash
#
# Run broadcasting routine.

DATE_STR=${1}
JOB_ID=$(uuidgen)

# Ensure directory exists for logs
OUTPUT_DIR=/scratch-shared/mycostreams/$JOB_ID
mkdir -p $OUTPUT_DIR

cd $HOME/pycode/mycostreams/slurm-uploader

BROADCAST_JOB_ID=$(sbatch \
    --parsable \
    --output "$OUTPUT_DIR/slurm-%A.out" \
    "./scripts/broadcast.sh" "$JOB_ID"\
)

echo $BROADCAST_JOB_ID >> "$OUTPUT_DIR/jobs.txt"

echo $JOB_ID
