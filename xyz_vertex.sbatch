#!/bin/sh

## FarmShare deployment file that requests 4 cpu cores for 24 hours to run xyz_ems.py
## xyz_vertex.py will request 32 4GiB cores.
#SBATCH --job-name=xyz_vertex
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=24:00:00
#SBATCH --error=xyz_vertex.err
#SBATCH --output=xyz_vertex.out

## Run the python script
time python3 ./xyz_vertex.py
