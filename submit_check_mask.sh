#!/usr/bin/env bash
#
# SLURM submission wrapper for run_check_mask.sh
#
# Usage (run from the repo root):
#   mkdir -p logs
#   sbatch submit_check_mask.sh IN_DIR SUFFIX OUT_DIR
#
# Example:
#   sbatch submit_check_mask.sh in/test T1 out/test
#
# stdout + stderr go to  logs/check_mask_<jobid>.log
#
#SBATCH --job-name=check_mask
#SBATCH --output=logs/check_mask_%j.log
#SBATCH --error=logs/check_mask_%j.log
#SBATCH --partition=short

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: sbatch $0 IN_DIR SUFFIX OUT_DIR" >&2
    exit 1
fi

# Move to the directory the job was submitted from (repo root).
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"

# --- Make `python` (with SimpleITK + numpy) available on the compute node ---
# Uncomment / edit whichever applies to your cluster:
# module load python/3.11
# source ~/miniconda3/etc/profile.d/conda.sh && conda activate check_mask
# source .venv/bin/activate

echo "Job $SLURM_JOB_ID starting on $(date)"
echo "Args: IN_DIR=$1  SUFFIX=$2  OUT_DIR=$3"

./run_check_mask.sh "$1" "$2" "$3"

echo "Job $SLURM_JOB_ID finished at $(date)"
