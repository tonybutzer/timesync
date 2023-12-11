cat:
	cat Makefile

clean:
	rm .out/*
	rm .job/*

1989: clean
	./pc_user.py --start_year 1989 --end_year 1989 lcnext_srs5000_final.csv


verify:
	grep -L Success .out/*.out
	ls .out/*.out | wc

