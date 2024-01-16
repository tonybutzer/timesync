#! /bin/bash

start_y='2000'
end_y='2000'

for ((year=start_y; year<=end_y; year++)); do {
	dest="/data/lcmap/www/storages/prj_202301"

	srccsv="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}"

	# run it twice to catch any simple errors
	for sub in b743 b432 ; do {
		#rsync -azv $srccsv $dest
		mkdir -p ${dest}/${year}/prj_1211/
		rsync -azv ${srccsv}/prj_1211/${sub} ${dest}/${year}/prj_1211/ &
	} done
} done

