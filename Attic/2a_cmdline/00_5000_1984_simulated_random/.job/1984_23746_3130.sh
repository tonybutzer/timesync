#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1984_23746_3130.job
#SBATCH --output=.out/1984_23746_3130.out
#SBATCH --error=.out/1984_23746_3130.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1984 --x -937470 --y 1899630 --plot_id 23746 3130