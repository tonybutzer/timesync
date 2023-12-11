#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1998_0215_3132.job
#SBATCH --output=.out/1998_0215_3132.out
#SBATCH --error=.out/1998_0215_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1998 --x -470400 --y 1298310 --plot_id 215 3132