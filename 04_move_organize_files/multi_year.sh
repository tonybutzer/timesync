#! /bin/bash

for yr in {1985..1987}; do echo $yr; python organize.py $yr; done
