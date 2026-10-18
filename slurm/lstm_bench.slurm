#!/bin/bash
#SBATCH -o %x-%J.out
#SBATCH -e %x-%J.error
#SBATCH --time=0-00:30:00
#SBATCH -n 1
#SBATCH --mem=8G

set -euo pipefail
module load tensorflow/2.5.0-cuda-system
cd "$SLURM_SUBMIT_DIR"
BENCH_MODE=$MODE python benchmarks/lstm_gpu_benchmark.py
