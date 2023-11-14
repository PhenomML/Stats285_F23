#!/bin/sh

#SBATCH --job-name=hw5_array
#SBATCH --partition=normal
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
#SBATCH --error=hw5_array.err
#SBATCH --output=hw5_array.out
#SBATCH --array=0-999:100
#SBATCH --nodes 1

#ml anaconda3/2023.07
#source activate stats285

#while [ $SLURM_ARRAY_TASK_ID -le $SLURM_ARRAY_TASK_MAX ]
for i in {0..9}
do
  srun -n 1 python3 ./map_function.py 1000 1000 $SLURM_ARRAY_TASK_ID su_id_hw5 &
done

wait # important to make sure the job doesn't exit before the background tasks are done
