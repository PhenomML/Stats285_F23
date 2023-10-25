#!/bin/sh

## farmshare deployment file that requests 4 cpu cores for 10 minutes to run hw2script.py
#SBATCH --job-name=hw3
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=00:10:00
#SBATCH --error=hw3.err
#SBATCH --output=hw3.out

## Run the python script
time python3 ~/Stats285_hw3/main.py