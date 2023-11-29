#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1990_0347_3132.job
#SBATCH --output=.out/1990_0347_3132.out
#SBATCH --error=.out/1990_0347_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1990 --x -531150 --y 1361040 --plot_id 347 3132