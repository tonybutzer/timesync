#! /bin/bash

start_y='2014'
end_y='2023'

for ((year=start_y; year<=end_y; year++)); do {

	dest="/data/lcmap/www/storages/prj_202301"

	srccsv="ec2-user@10.12.71.200:/efs/timesync/${year}"

	time rsync -azv ${srccsv} ${dest}
} done

