#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=2001_0338_3132.job
#SBATCH --output=.out/2001_0338_3132.out
#SBATCH --error=.out/2001_0338_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 2001 --x -466500 --y 1295340 --plot_id 338 3132