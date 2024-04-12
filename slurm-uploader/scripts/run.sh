#!/bin/bash
#
# Run archiving routine.

DATE_STR=${1}
JOB_ID=$(uuidgen)

# Ensure directory exists for logs
OUTPUT_DIR=/scratch-shared/$USER/$JOB_ID
mkdir -p $OUTPUT_DIR

cd $HOME/mycostreams/slurm-uploader

ARCHIVE_JOB_ID=$(sbatch \
    --parsable \
    --output "$OUTPUT_DIR/slurm-%A.out" \
    "./scripts/archive.sh" "$DATE_STR"\
)

echo $JOB_ID
