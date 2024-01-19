#! /bin/bash

start_y='2004'
end_y='2004'

for ((year=start_y; year<=end_y; year++)); do {
	#dest="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}/"
	home='./timesync/'
	dest="butzer@tallgrass.cr.usgs.gov:./timesync/"

	srccsv="/efs/timesync/${year}/"

	# run it twice to catch any simple errors
	#rsync -azv $srccsv $dest &
	#rsync -azv $srccsv $dest
	
	 for sub in b743 b432 tc; do {
                #rsync -azv $srccsv $dest
                ssh butzer@tallgrass.cr.usgs.gov mkdir -p ${home}/${year}/prj_1211/
                rsync -azv ${srccsv}/prj_1211/${sub} ${dest}/${year}/prj_1211/ &
        } done

} done



