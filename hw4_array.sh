#!/bin/sh

#SBATCH --job-name=hw4_array
#SBATCH --partition=normal
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --error=hw4_array.err
#SBATCH --output=hw4_array.out
#SBATCH --array=0-999:100
#SBATCH --nodes 1

for i in {0..9}
do
  srun -n 1 python3 ~/Stats285_hw3/map_function.py 1000 1000 $((SLURM_ARRAY_TASK_ID)) test_batch_4 &
done

wait # important to make sure the job doesn't exit before the background tasks are done
