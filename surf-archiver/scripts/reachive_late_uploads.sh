#!/bin/bash
#SBATCH --job-name=reachive_late
#SBATCH --partition=staging
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2-00:00:00
#SBATCH --output=reachive_late_%j.out
#SBATCH --mail-type=FAIL,END --mail-user=s.vstaalduine@amolf.nl
#
# One-off: archive S3 image files that reached S3 after their day's tar was written.
#
# `surf-archiver` writes one `<experiment>/<YYYYMMDD>.tar` per day and skips any day whose tar
# already exists, so files uploaded later (e.g. ART2504A107/20250531: tar at 01:40, 21 of 24
# files uploaded ~06:00) are in S3 only. For each listed day this writes the files the original
# tar lacks into `<YYYYMMDD>.late.tar` next to it. The original tar is never touched, and
# nothing in S3 is tagged or deleted -- deletion is a separate decision once this has run.
#
# "Lacks" = a (name, size) pair in S3 that is not in the tar, so a file re-uploaded with a
# different size is archived again; the original keeps the old version.
#
# Usage (dry run is the default; it lists, downloads nothing, writes nothing):
#   sbatch reachive_late_uploads.sh ~/reachive/groups.txt
#   DRY_RUN=0 sbatch --export=ALL reachive_late_uploads.sh ~/reachive/groups.txt
# groups.txt: one `<experiment>/<YYYYMMDD>` per line.
set -euo pipefail
export LC_ALL=C   # `comm` needs both listings sorted the same way

GROUP_LIST=${1:?usage: reachive_late_uploads.sh <groups file>}
DRY_RUN=${DRY_RUN:-1}
SRC=ceph-s3:mycostreams-raw-data/images
DST=/archive/mycostreams/raw-data/images
WORK=/scratch-shared/$USER/reachive_work
MANIFEST=$HOME/reachive/manifest.tsv   # group, files, bytes, late tar, time
mkdir -p "$WORK" "$(dirname "$MANIFEST")"

listing() {  # GNU `tar -tvf` -> "name<TAB>size", names without the "./" the archiver writes
    tar -tvf "$1" | awk '{n=$NF; sub(/^\.\//, "", n); if (n != "" && n != ".") print n "\t" $3}' | sort
}

while read -r g; do
    [ -z "$g" ] && continue
    e=${g%/*}; d=${g#*/}
    orig=$DST/$e/$d.tar; late=$DST/$e/$d.late.tar; w=$WORK/$e/$d
    if [ -e "$late" ]; then echo "skip    $g: $late exists"; continue; fi
    if [ ! -e "$orig" ]; then echo "ERROR   $g: no original tar $orig"; continue; fi

    mkdir -p "$w"
    listing "$orig" > "$w.in_tar"
    rclone lsf --files-only --format ps --separator $'\t' "$SRC/$g/" | sort > "$w.in_s3"
    comm -13 "$w.in_tar" "$w.in_s3" > "$w.missing"
    n=$(wc -l < "$w.missing")
    bytes=$(awk -F'\t' '{s += $2} END {print s + 0}' "$w.missing")
    if [ "$n" -eq 0 ]; then echo "ok      $g: original tar holds every S3 file"; rm -rf "$w" "$w".*; continue; fi
    if [ "$DRY_RUN" != 0 ]; then echo "would   $g: $n files, $bytes bytes"; continue; fi

    # rclone checks size and checksum on every copy, so a short download fails here, not later
    cut -f1 "$w.missing" > "$w.names"
    rclone copy --files-from "$w.names" --transfers 4 "$SRC/$g/" "$w/"
    tar -cf "$late.part" -C "$w" .
    if ! diff -q <(listing "$late.part") "$w.missing" > /dev/null; then
        echo "ERROR   $g: $late.part does not match the missing list, left in place"; continue
    fi
    mv "$late.part" "$late"
    printf '%s\t%s\t%s\t%s\t%s\n' "$g" "$n" "$bytes" "$late" "$(date '+%F %T')" >> "$MANIFEST"
    echo "wrote   $g: $n files, $bytes bytes -> $late"
    rm -rf "$w" "$w".*
done < "$GROUP_LIST"
