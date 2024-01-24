#! /bin/bash

for yr in {1988..1999}; do {
	echo $yr; 
        python organize_b432_b743_tc.py $yr; 
        python handle_csv.py $yr; 
} done
