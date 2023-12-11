#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1996_0235_3132.job
#SBATCH --output=.out/1996_0235_3132.out
#SBATCH --error=.out/1996_0235_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1996 --x -477750 --y 1322640 --plot_id 235 3132