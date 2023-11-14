#!/bin/sh

## farmshare deployment file that requests 16 cpu cores for 15 minutes to run main.py
#SBATCH --job-name=hw5_large
#SBATCH --partition=normal
#SBATCH --cpus-per-task=16
#SBATCH --time=00:15:00
#SBATCH --error=hw5_dask_large.err
#SBATCH --output=hw5_dask_large.out


## Run the python script
time python3 ./main.py
