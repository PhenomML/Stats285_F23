#!/bin/sh

## farmshare deployment file that requests 8 cpu cores for 30 minutes to run main.py
#SBATCH --job-name=hw4_cluster
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --error=hw4_cluster.err
#SBATCH --output=hw4_cluster.out

## Run the python script
time python3 ~/Stats285_hw3/main.py