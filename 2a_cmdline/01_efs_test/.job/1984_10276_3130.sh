#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1984_10276_3130.job
#SBATCH --output=.out/1984_10276_3130.out
#SBATCH --error=.out/1984_10276_3130.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1984 --x 577710 --y 881160 --plot_id 10276 3130