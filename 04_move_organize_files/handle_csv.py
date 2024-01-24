# this python will organize the subdirs into bigger directories


# Write the command line parser

import sys
import os
import pandas as pd
import shutil
import time
from tqdm import tqdm

print (sys.argv[1])

my_year = sys.argv[1]

SRC_DIR = f'/data/lcmap/www/storages/00_from_cloud_headnode/timesync/{my_year}/prj_1211'

DEST_DIR = '/data/lcmap/www/storages/prj_202301'

print ('SRC_DIR:', SRC_DIR)
print ('DEST_DIR:', DEST_DIR)


# Specify the directory containing your CSV files
directory_path = SRC_DIR

# Get a list of all CSV files in the directory
csv_files = [file for file in os.listdir(directory_path) if file.endswith('.csv')]

# Initialize an empty DataFrame to store the concatenated data
concatenated_df = pd.DataFrame()

# Loop through each CSV file and concatenate its data to the main DataFrame
for i in tqdm(range(0,len(csv_files))):
#for csv_file in csv_files:
    csv_file = csv_files[i]
    file_path = os.path.join(directory_path, csv_file)
    df = pd.read_csv(file_path)
    concatenated_df = pd.concat([concatenated_df, df], ignore_index=True)
    #print(".",flush=True, end="")

# Write the concatenated DataFrame to a new CSV file
concatenated_df.insert(0,'project_id1', '202301')
output_csv_path = f'{DEST_DIR}/{my_year}_prj_202301_region_spectrals.csv'

sorted_df = concatenated_df.sort_values(by=['plot_id', 'doy'])
sorted_df.to_csv(output_csv_path, index=False, header=False)

print(f"Concatenated data written to {output_csv_path}")
