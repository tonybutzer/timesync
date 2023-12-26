cat:
	cat Makefile

clean:
	rm .out/*
	rm .job/*

1984: 
	./pc_user.py --start_year 1984 --end_year 1984 lcnext_srs5000_final.csv

1985: clean
	./pc_user.py --start_year 1985 --end_year 1985 lcnext_srs5000_final.csv


test3:
	python3 ts_user.py --year 1998 --plot_id 1 --x -530580 --y 1318380  1222



verify:
	grep -L Success .out/*.out
	ls .out/*.out | wc

