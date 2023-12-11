#! /bin/bash
#

for year in {1995..1995}; do 
	echo $year;  
	./pc_user.py --start_year $year --end_year $year Big_Plot_List.csv
done

