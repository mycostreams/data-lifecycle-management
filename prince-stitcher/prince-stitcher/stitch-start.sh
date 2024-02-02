
#! /usr/bin/env bash
set -e

if [ -z $FOLDER ]
then
    echo "FOLDER required"
else 
    exec ImageJ-linux64 --headless --default-gc --ij2 -macro ./scripts/stitch.ijm ${FOLDER}
fi
