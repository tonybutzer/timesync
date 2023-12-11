#! /bin/bash

start_y='1987'
end_y='1989'

for ((year=start_y; year<=end_y; year++)); do {
	dest="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}/"

	srccsv="/efs/timesync/${year}/"

	# run it twice to catch any simple errors
	rsync -azv -e 'ssh -J ec2-user@10.12.71.52' $srccsv $dest
	rsync -azv -e 'ssh -J ec2-user@10.12.71.52' $srccsv $dest
} done



