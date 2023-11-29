#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1997_0117_3132.job
#SBATCH --output=.out/1997_0117_3132.out
#SBATCH --error=.out/1997_0117_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1997 --x -491580 --y 1334970 --plot_id 117 3132