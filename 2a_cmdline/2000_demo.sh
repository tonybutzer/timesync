#! /bin/bash
#

for year in {2000..2003}; do 
	echo $year;  
	./pc_user.py --start_year $year --end_year $year Big_Plot_List.csv
done

