cat:
	cat Makefile


MFORGE=al2-mambaforge
mforge:
	docker build -t ${MFORGE} .

mrun:
	docker run -it ${MFORGE} bash


BASE=timesync-base

base:
	docker build -t ${BASE} -f Dockerfile.base .


run:
	docker run -it ${BASE} bash
