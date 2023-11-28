#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=0139_3132.job
#SBATCH --output=.out/0139_3132.out
#SBATCH --error=.out/0139_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1987 --x -582990 --y 1221390 --plot_id 139 3132