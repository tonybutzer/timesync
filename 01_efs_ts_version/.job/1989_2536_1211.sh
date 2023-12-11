#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name=1989_2536_1211.job
#SBATCH --output=.out/1989_2536_1211.out
#SBATCH --error=.out/1989_2536_1211.err
source /efs/mambaforge/bin/activate city
python3 ts_user.py --year 1989 --x 1360890 --y 1435650 --plot_id 2536 1211