#!/bin/sh

## farmshare deployment file that requests 4 cpu cores for 10 minutes to run hw2script.py
#SBATCH --job-name=hw2
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=00:10:00
#SBATCH --error=hw2.err
#SBATCH --output=hw2.out

## Load the python module
#module load anaconda3/2023.07
ml python/3.11.4

## Run the python script
time python3 ~/Stats285_hw3/main.py