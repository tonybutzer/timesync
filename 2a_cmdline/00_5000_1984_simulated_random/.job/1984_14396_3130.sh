#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1984_14396_3130.job
#SBATCH --output=.out/1984_14396_3130.out
#SBATCH --error=.out/1984_14396_3130.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1984 --x 1390920 --y 1920690 --plot_id 14396 3130