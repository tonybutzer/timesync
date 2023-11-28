#!/usr/bin/env python
# coding: utf-8


import os
import pandas as pd
import argparse

def get_slurm_text(full_python_cmd, job_name):
    lizard = job_name
    slurm_text = f'''#!/bin/bash
#SBATCH --account=butzer
#SBATCH --time=00:20:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=butzer@contractor.usgs.gov
#SBATCH --job-name={lizard}.job
#SBATCH --output=.out/{lizard}.out
#SBATCH --error=.out/{lizard}.err
source /efs/mambaforge/bin/activate city
{full_python_cmd}'''
    return slurm_text

def write_job(slurm_text, city):
    jn = f'.job/{city}.sh'
    f= open(jn,"w+")
    f.write(slurm_text)
    f.close
    return jn

def sbatch_job(job):
    print(job)
    cmd = f'sbatch {job}'
    os.system(cmd)

def make_cmd(plot_id, year, x, y, project_id):
    arguments = f'--year {year} --x {x} --y {y} --plot_id {plot_id} {project_id}'

    return f'python3 ts_user.py {arguments}'

def do_job(plot_id, year, x, y, project_id):
    cmd = f'python3 ts_user.py --'
    cmd = make_cmd(plot_id, year, x, y, project_id)
    print(cmd)
    number_str = str(plot_id).zfill(4)
    job_name=f"{number_str}_{project_id}"
    print(job_name)
    slurm_text = get_slurm_text(cmd, job_name)
    job = write_job(slurm_text, job_name)
    sbatch_job(job)


def _mkdir(directory):
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)

def get_parser():
    parser = argparse.ArgumentParser(description='Run the parallel cluster timesync code')
    parser.add_argument('plot_file', metavar='plot_file', type=str, 
            help='the plot_file with 500 to 5000 plot_ids ')
    parser.add_argument('-s', '--start_year', help='start year -s 1999 ', default='1984', type=str, required=True)
    parser.add_argument('-e', '--end_year', help='end year for plots for timesync', type=str, required=True)
    return parser

def run_parallel_cluster(plot_file, start_year, end_year):
    print (plot_file, start_year, end_year)
    df = pd.read_csv('Big_Plot_List.csv')

    for i,r in df.iterrows():
        print(r'plot_id')
        project_id = r['project_id']
        plot_id = r['plot_id']
        x = r['x']
        y = r['y']
        Strata = r['Strata']
        do_job(plot_id, start_year, x, y, project_id)



def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())


    print(args)

    _mkdir('.out')
    _mkdir('.job')

    plot_file = args['plot_file']
    start_year=args['start_year']
    end_year=args['end_year']

    run_parallel_cluster(plot_file, start_year, end_year)

    return True


if __name__ == '__main__':

    command_line_runner()
