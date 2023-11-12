#!/bin/sh

## farmshare deployment file that requests 4 cpu cores for 30 minutes to run main.py
#SBATCH --job-name=hw5_cluster
#SBATCH --partition=normal,owners,donoho,hns,stat
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --error=hw5_cluster.err
#SBATCH --output=hw5_cluster.out

## Run the python script
time python3 ./main.py
