"""Merge the per-study all_voxels.csv files into a single CSV.

Each study is expected to have its own output folder produced by
run_check_mask.sh, e.g.

    out/study_a/all_voxels.csv
    out/study_b/all_voxels.csv

This script concatenates those files, adds a `study` column (the name of
the folder containing each file), sorts by n_components descending, and
writes one combined CSV.

Usage:
    python merge_studies.py --out_root out --out out/merged_voxels.csv
    python merge_studies.py --in out/a/all_voxels.csv out/b/all_voxels.csv --out merged.csv
"""

import argparse
import glob
import os
import sys

import pandas as pd

DEFAULT_NAME = "all_voxels.csv"


def collect_paths(args):
    if args.in_paths:
        return list(args.in_paths)
    pattern = os.path.join(args.out_root, "*", args.name)
    return sorted(glob.glob(pattern))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out_root",
        default="out",
        help="Folder containing one subfolder per study (default: out)",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_NAME,
        help=f"Per-study file name to merge (default: {DEFAULT_NAME})",
    )
    parser.add_argument(
        "--in",
        dest="in_paths",
        nargs="+",
        help="Explicit list of CSV paths to merge (overrides --out_root)",
    )
    parser.add_argument("--out", required=True, help="Path for the merged CSV")
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Sort n_components ascending instead of descending",
    )
    args = parser.parse_args()

    paths = collect_paths(args)
    if not paths:
        sys.exit(f"ERROR: no files to merge (looked for {args.out_root}/*/{args.name})")

    frames = []
    for path in paths:
        study = os.path.basename(os.path.dirname(os.path.abspath(path)))
        df = pd.read_csv(path)
        df.insert(0, "study", study)
        frames.append(df)
        print(f"  {study}: {len(df)} rows from {path}")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values(
        "n_components", ascending=args.ascending, kind="stable"
    ).reset_index(drop=True)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    merged.to_csv(args.out, index=False)
    print(f"Wrote {len(merged)} rows -> {args.out}")


if __name__ == "__main__":
    main()
