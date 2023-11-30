#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=2001_0120_3132.job
#SBATCH --output=.out/2001_0120_3132.out
#SBATCH --error=.out/2001_0120_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 2001 --x -477150 --y 1320540 --plot_id 120 3132