#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=2003_0085_3132.job
#SBATCH --output=.out/2003_0085_3132.out
#SBATCH --error=.out/2003_0085_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 2003 --x -528390 --y 1353360 --plot_id 85 3132