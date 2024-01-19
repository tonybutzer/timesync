#! /bin/bash

start_y='2012'
end_y='2012'

for ((year=start_y; year<=end_y; year++)); do {
	dest="/data/lcmap/www/storages/prj_202301"

	#srccsv="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}"
	srccsv="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/eros/usmart/timesync/${year}"
	#srccsv="butzer@tallgrass.cr.usgs.gov:timesync/${year}"

	time rsync -azv ${srccsv} ${dest}
} done

