#! /bin/bash

start_y='2001'
end_y='2001'

for ((year=start_y; year<=end_y; year++)); do {
	dest="/data/lcmap/www/storages/prj_202301"

	# srccsv="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}"
	srccsv="butzer@tallgrass.cr.usgs.gov:timesync/${year}"

	rsync -azv ${srccsv} ${dest}
} done
