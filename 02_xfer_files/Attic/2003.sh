#! /bin/bash

start_y='2003'
end_y='2003'

for ((year=start_y; year<=end_y; year++)); do {
	dest="/data/lcmap/www/storages/prj_202301/timesync"

	# srccsv="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}"
	srccsv="butzer@tallgrass.cr.usgs.gov:timesync/${year}"

	rsync -azv ${srccsv} ${dest}
} done

