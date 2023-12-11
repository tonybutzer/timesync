#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1989_3019_1211.job
#SBATCH --output=.out/1989_3019_1211.out
#SBATCH --error=.out/1989_3019_1211.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1989 --x -1663410 --y 2237490 --plot_id 3019 1211