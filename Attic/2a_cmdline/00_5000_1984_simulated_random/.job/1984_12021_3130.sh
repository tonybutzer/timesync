#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1984_12021_3130.job
#SBATCH --output=.out/1984_12021_3130.out
#SBATCH --error=.out/1984_12021_3130.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1984 --x -1616580 --y 2050440 --plot_id 12021 3130