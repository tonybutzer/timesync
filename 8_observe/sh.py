#!/usr/bin/env python
# coding: utf-8
# tony

import subprocess
import pandas as pd
from tabulate import tabulate

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

def main():
    # Run squeue command and get the output
    squeue_output, _ = run_command('squeue')

    # Parse squeue output into a DataFrame
    df = parse_squeue_output(squeue_output)

    filtered_df = df[df['ST'] == 'R']

    # Display the DataFrame nicely on the terminal
    display_dataframe(filtered_df.head())

    # Display state counts
    display_state_counts(df)

if __name__ == "__main__":
    main()


