#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=0268_3132.job
#SBATCH --output=.out/0268_3132.out
#SBATCH --error=.out/0268_3132.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1987 --x -467400 --y 1328700 --plot_id 268 3132