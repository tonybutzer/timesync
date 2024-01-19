#! /bin/bash

start_y='2002'
end_y='2002'

for ((year=start_y; year<=end_y; year++)); do {
	dest="butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/${year}/"
	#dest="butzer@tallgrass.cr.usgs.gov:./timesync/${year}/"

	srccsv="/efs/timesync/${year}/"

	# run it twice to catch any simple errors
	rsync -azv $srccsv $dest &
	#rsync -azv $srccsv $dest
	
	 for sub in b743 b432 tc; do {
                #rsync -azv $srccsv $dest
                mkdir -p ${dest}/${year}/prj_1211/
                rsync -azv --mkpath ${srccsv}/prj_1211/${sub} ${dest}/${year}/prj_1211/ &
        } done

} done



