#!/bin/sh

## farmshare deployment file that requests 16 cpu cores for 10 minutes to run main.py
#SBATCH --job-name=hw5
#SBATCH --partition=normal
#SBATCH --cpus-per-task=16
#SBATCH --time=00:15:00
#SBATCH --error=hw5.err
#SBATCH --output=hw5.out


## Run the python script
time python3 ~/Stats285_hw3/main.py