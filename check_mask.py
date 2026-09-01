"""Check a binary ICV mask by analyzing its connected components.

Reads a mask, extracts connected components (sorted by size, largest first)
and writes two head-less, single-row CSVs:

    {out_prefix}_voxels.csv   component sizes in voxels
    {out_prefix}_volume.csv   component sizes in mm^3

Row layout (no header), identical in both files:

    img_name, n_components,
    comp1, comp_others, comp2, comp3, ... comp10

where comp_others is the total size of every component except the largest.
comp2..comp10 are zero-padded when there are fewer components.

The total number of connected components is also printed to stdout.
"""

import argparse
import os
import sys

import numpy as np
import SimpleITK as sitk

# Number of ranked component columns (comp1..comp10).
TOP_N = 10


def analyze_mask(in_mask):
    """Return (voxel_counts, voxel_volume_mm3, n_components) for a mask path.

    voxel_counts is a 1-D array with the voxel count of every component,
    ordered largest-first.
    """
    mask = sitk.ReadImage(in_mask)

    # Same approach as the in-place correction snippet: label connected
    # components and relabel them so label 1 is the largest, 2 the next, etc.
    components = sitk.ConnectedComponent(mask)
    sorted_components = sitk.RelabelComponent(components, sortByObjectSize=True)

    arr = sitk.GetArrayFromImage(sorted_components)
    labels = arr[arr > 0]
    n_components = int(labels.max()) if labels.size else 0

    # Voxel counts per label, ordered by rank (label value).
    voxel_counts = np.bincount(labels, minlength=n_components + 1)[1:]

    voxel_volume_mm3 = float(np.prod(mask.GetSpacing()))
    return voxel_counts, voxel_volume_mm3, n_components


def build_row(img_name, sizes, n_components):
    """Build the single CSV row for the given per-component sizes.

    sizes is largest-first; length == n_components.
    """
    largest = sizes[0] if n_components >= 1 else 0
    others = sizes[1:].sum() if n_components >= 1 else 0

    ranked = []
    for rank in range(1, TOP_N + 1):
        ranked.append(sizes[rank - 1] if rank <= n_components else 0)

    # img_name, n_components, comp1, comp_others, comp2, comp3, ... comp10
    row = [img_name, n_components, largest, others] + ranked[1:]
    return row


def format_value(v):
    if isinstance(v, str):
        return v
    if float(v).is_integer():
        return str(int(v))
    return repr(float(v))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in_mask", required=True, help="Path to the input mask (.nii.gz)")
    parser.add_argument(
        "--out_prefix",
        required=True,
        help="Output path prefix; writes {prefix}_voxels.csv and {prefix}_volume.csv",
    )
    args = parser.parse_args()

    if not os.path.exists(args.in_mask):
        sys.exit(f"ERROR: input mask not found: {args.in_mask}")

    img_name = os.path.basename(args.in_mask)
    voxel_counts, voxel_volume_mm3, n_components = analyze_mask(args.in_mask)

    voxel_sizes = voxel_counts.astype(np.int64)
    volume_sizes = voxel_counts.astype(np.float64) * voxel_volume_mm3

    out_dir = os.path.dirname(os.path.abspath(args.out_prefix))
    os.makedirs(out_dir, exist_ok=True)

    for suffix, sizes in (("voxels", voxel_sizes), ("volume", volume_sizes)):
        row = build_row(img_name, sizes, n_components)
        out_path = f"{args.out_prefix}_{suffix}.csv"
        with open(out_path, "w") as f:
            f.write(",".join(format_value(v) for v in row) + "\n")

    # Print the number of connected components as the last line of stdout.
    print(n_components)


if __name__ == "__main__":
    main()
