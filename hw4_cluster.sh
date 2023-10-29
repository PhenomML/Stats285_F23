#!/bin/sh

## farmshare deployment file that requests 8 cpu cores for 30 minutes to run main.py
#SBATCH --job-name=hw4
#SBATCH --partition=normal
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --error=hw4.err
#SBATCH --output=hw4.out

## Run the python script
time python3 ~/Stats285_hw3/main.py