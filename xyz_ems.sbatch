#!/bin/sh

## FarmShare deployment file that requests 4 cpu cores for 24 hours to run xyz_ems.py
## xyz_ems.py will request 16 4GiB cores.
#SBATCH --job-name=xyz_ems
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=24:00:00
#SBATCH --error=xyz_ems.err
#SBATCH --output=xyz_ems.out

## Run the python script
time python3 ./xyz_ems.py
