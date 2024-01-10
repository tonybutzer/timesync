#!/usr/bin/env python
# coding: utf-8

import os
from loguru import logger
import subprocess
import pandas as pd
from tabulate import tabulate
import time

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout, result.stderr

def parse_squeue_output(output):
    # Assuming squeue output format: JOBID, PARTITION, NAME, USER, STATE, TIME, NODES, CPUS
    lines = output.strip().split('\n')
    headers = lines[0].split()
    data = [line.split() for line in lines[1:]]
    df = pd.DataFrame(data, columns=headers)
    return df

def display_dataframe(df):
    # Display the DataFrame using tabulate
    print(tabulate(df, headers='keys', tablefmt='fancy_grid'))

def display_state_counts(df):
    # Count occurrences of each unique state (ST)
    state_counts = df['ST'].value_counts()

    # Display the counts
    print("\nState Counts:")
    print(tabulate(state_counts.reset_index(), headers=['STATE', 'Count'], tablefmt='fancy_grid', showindex=False))

def mainwait():

    are_we_there_yet = False
    while not are_we_there_yet:
        # Run squeue command and get the output
        squeue_output, _ = run_command('squeue')

        # Parse squeue output into a DataFrame
        df = parse_squeue_output(squeue_output)
    
        filtered_df = df[df['ST'] == 'R']

        # Display the DataFrame nicely on the terminal
        #display_dataframe(filtered_df.head())

        # Display state counts
        #display_state_counts(df)

        if df.shape[0] > 0:
            are_we_there_yet = False
            print('.', end='', flush=True)
            time.sleep(30)
        else:
            are_we_there_yet = True


def clean():
	os.system('rm .out/*')
	os.system('rm .job/*')


def verify(year):
    # Define the directory path
    directory_path = '.out'

    # Get a list of all files in the directory with a .out extension
    files = [f for f in os.listdir(directory_path) if f.endswith('.out')]

    # Loop through each file
    for file in files:
        file_path = os.path.join(directory_path, file)

        # Check if the file contains the word 'Success'
        with open(file_path, 'r') as f:
            file_content = f.read()
            if 'Success' not in file_content:
                msg = f"{year} The file {file} does not contain the word 'Success'"
                logger.error(msg)
    if (len(files) < 5000):
        print('Less than 5000 files found')
        logger.error(f'{year} Less than 5000 files found')



# Configure Loguru to write logs to a file
logger.add("0_run_decade.log", level="INFO", rotation="1 day", retention="7 days")

clean()

for year in range(1995, 1999+1):
    print(year)
    cmd = f'./pc_user.py --start_year {year} --end_year {year} lcnext_srs5000_final.csv'
    os.system(cmd)
    mainwait()
    verify(year)
