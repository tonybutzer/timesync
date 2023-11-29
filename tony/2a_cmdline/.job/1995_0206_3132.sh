#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1995_0206_3132.job
#SBATCH --output=.out/1995_0206_3132.out
#SBATCH --error=.out/1995_0206_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1995 --x -591720 --y 1308330 --plot_id 206 3132