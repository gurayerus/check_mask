#!/usr/bin/env bash
#
# Run check_mask.py on every mask in a folder.
#
# Masks are expected to be named  {MRID}_{SUFFIX}.nii.gz
# For each mask, two CSVs are written to OUT_DIR:
#   {MRID}_{SUFFIX}_voxels.csv   component sizes in voxels
#   {MRID}_{SUFFIX}_volume.csv   component sizes in mm^3
# A mask is skipped when both of its CSVs already exist.
#
# When all masks are done, the per-mask CSVs are concatenated into:
#   OUT_DIR/all_voxels.csv
#   OUT_DIR/all_volume.csv
# each with a header row and sorted by comp_others (column 4) descending.
#
# Usage:
#   ./run_check_mask.sh IN_DIR SUFFIX OUT_DIR
#
# Example:
#   ./run_check_mask.sh in/test T1 out/test

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 IN_DIR SUFFIX OUT_DIR" >&2
    echo "Example: $0 in/test T1 out/test" >&2
    exit 1
fi

IN_DIR="$1"
SUFFIX="$2"
OUT_DIR="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "$IN_DIR" ]]; then
    echo "ERROR: input directory not found: $IN_DIR" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

shopt -s nullglob
masks=("$IN_DIR"/*_"$SUFFIX".nii.gz)
shopt -u nullglob

if [[ ${#masks[@]} -eq 0 ]]; then
    echo "ERROR: no files matching *_${SUFFIX}.nii.gz in $IN_DIR" >&2
    exit 1
fi

HEADER="img_name,n_components,comp1,comp_others,comp2,comp3,comp4,comp5,comp6,comp7,comp8,comp9,comp10"

voxels_csvs=()
volume_csvs=()

for mask in "${masks[@]}"; do
    fname="$(basename "$mask")"
    mrid="${fname%_${SUFFIX}.nii.gz}"
    out_prefix="$OUT_DIR/${mrid}_${SUFFIX}"
    out_voxels="${out_prefix}_voxels.csv"
    out_volume="${out_prefix}_volume.csv"

    if [[ -f "$out_voxels" && -f "$out_volume" ]]; then
        echo "Skipping $fname (CSVs already exist)"
    else
        echo "Processing $fname ..."
        n_components="$(python "$SCRIPT_DIR/check_mask.py" --in_mask "$mask" --out_prefix "$out_prefix" | tail -n 1)"
        echo "  -> ${out_prefix}_{voxels,volume}.csv  (n_components=${n_components})"
    fi

    voxels_csvs+=("$out_voxels")
    volume_csvs+=("$out_volume")
done

# Concatenate per-mask CSVs, add a header, sort by comp_others (col 4) descending.
concat_sorted() {
    local out_file="$1"; shift
    { echo "$HEADER"; cat "$@" | sort -t, -k4 -g -r; } > "$out_file"
    echo "  -> $out_file"
}

echo "Concatenating ..."
concat_sorted "$OUT_DIR/all_voxels.csv" "${voxels_csvs[@]}"
concat_sorted "$OUT_DIR/all_volume.csv" "${volume_csvs[@]}"

echo "Done. Per-mask CSVs and all_{voxels,volume}.csv written to $OUT_DIR"
