#! /bin/bash

start_y='2006'
end_y='2006'

for ((year=start_y; year<=end_y; year++)); do {
	dest="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/eros/usmart/timesync/${year}/"
	#dest="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}/"
	#dest="butzer@tallgrass.cr.usgs.gov:./timesync/${year}/"

	srccsv="/efs/timesync/${year}/"

	# run it twice to catch any simple errors
	time rsync -azv $srccsv $dest &
	#rsync -azv $srccsv $dest
} done



