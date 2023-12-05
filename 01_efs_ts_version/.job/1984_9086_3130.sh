#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1984_9086_3130.job
#SBATCH --output=.out/1984_9086_3130.out
#SBATCH --error=.out/1984_9086_3130.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1984 --x -1694580 --y 1376340 --plot_id 9086 3130