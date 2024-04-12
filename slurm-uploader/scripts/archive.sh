#!/bin/bash
#
#SBATCH --partition=staging
#
# Archive all images for a given day. 
# Step 1: Download all images for a given day
# Step 2: Insert them into a per experiment archive
#
# TODO: Delete files when complete.

while getopts "d:" opt; do
   case "$opt" in
       d) DATE_STR=${OPTARG};;
   esac
done


DOWNLOAD_DIR=$(mktemp -d -p /scratch-shared)
ARCHIVE_DIR="/archive/$USER/"
TARGET_FILE=$DATE_STR.tar

echo "Copying data to temp dir: $DOWNLOAD_DIR"

# Download the data
rclone copy swift:prince-data-dev "$DOWNLOAD_DIR" --include "*/$DATE_STR*.tar"

if [ "$(ls -A $DOWNLOAD_DIR)" ]; then
    for EXPERIMENT_DIR in ${DOWNLOAD_DIR}/*/; 
    do
        EXPERIMENT_ID=$(basename $EXPERIMENT_DIR)
        TARGET_DIR=$ARCHIVE_DIR/$EXPERIMENT_ID

        echo "Creating archive: $TARGET_DIR/$TARGET_FILE"

        # mkdir -p "$TARGET_DIR"
        # tar -cf "$TARGET_DIR/$TARGET_FILE" -C "$DOWNLOAD_DIR" "$EXPERIMENT_ID"
    done    
    exit 0
else
    echo "No files downloaded"
    exit 1
fi

trap "rm -rf $DOWNLOAD_DIR" EXIT
