#!/bin/sh

## farmshare deployment file that requests 8 cpu cores for 30 minutes to run main.py
#SBATCH --job-name=hw4
#SBATCH --partition=normal
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --error=hw4.err
#SBATCH --output=hw4.out
#SBATCH --array=0-999:100
#SBATCH --n 10

## Run the python script
for i in {0..9}; do
  srun -n 1 python3 ~/Stats285_hw3/main.py 1000 1000 $((SLURM_ARRAY_TASK_ID+i*100)) test_batch &
done

wait # important to make sure the job doesn't exit before the background tasks are done
