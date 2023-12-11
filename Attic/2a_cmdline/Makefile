cat:
	cat Makefile

test:
	python3 ts_user.py --plot_id 2 --x -530580 --y 1318380  3132

test1:
	python3 ts_user.py --year 1990 --plot_id 1 --x -530580 --y 1318380  3132

test2:
	python3 ts_user.py --year 1995 --plot_id 1 --x -530580 --y 1318380  3132


test3:
	python3 ts_user.py --year 1998 --plot_id 1 --x -530580 --y 1318380  3132

profile:
	python3 -m scalene ts_user.py --year 1996 --plot_id 1 --x -530580 --y 1318380  3132

phtml:
	scalene --html --outfile a.html ts_user.py --year 1997 --plot_id 1 --x -530580 --y 1318380  3132

cout:
	rm -fr .out/*

flowchart:
	pyan3 -c --dot ts_process_group.py |dot -Tsvg -o a.svg
	pyan3 -c --dot ts_process_group.py |dot -Tpng -o a.png


graphviz:
	sudo yum install -y graphviz
