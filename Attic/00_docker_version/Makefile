cat:
	cat Makefile


IMAGE='chipper-image'
build:
	docker build -t ${IMAGE} .


run:
	docker run -it ${IMAGE} bash

clean:
	rm .out/*
	rm .job/*

1989: clean
	./pc_user.py --start_year 1989 --end_year 1989 lcnext_srs5000_final.csv


verify:
	grep -L Success .out/*.out
	ls .out/*.out | wc


test:
	python3 ts_user.py --plot_id 2 --x -530580 --y 1318380  3132

test1:
	python3 ts_user.py --year 1990 --plot_id 1 --x -530580 --y 1318380  3132

test2:
	python3 ts_user.py --year 1995 --plot_id 1 --x -530580 --y 1318380  3132


