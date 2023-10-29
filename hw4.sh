#!/bin/sh

## farmshare deployment file that requests 4 cpu cores for 10 minutes to run main.py
#SBATCH --job-name=hw4
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=00:10:00
#SBATCH --error=hw4.err
#SBATCH --output=hw4.out

## Run the python script
time python3 ~/Stats285_hw3/main.py