# this python will organize the subdirs into bigger directories


# Write the command line parser

import sys
import os
import shutil
import time

print (sys.argv[1])

my_year = sys.argv[1]

SRC_DIR = f'/data/lcmap/www/storages/00_from_cloud_test/timesync/{my_year}/prj_1211'

DEST_DIR = '/data/lcmap/www/storages/prj_202301'

print ('SRC_DIR:', SRC_DIR)
print ('DEST_DIR:', DEST_DIR)



def move_directory(source_path, destination_path):
    # Move the entire directory from source_path to destination_path
    shutil.move(source_path, destination_path)

def list_subdirectories(directory):
    subdirectories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return subdirectories

# Replace 'your_directory_path' with the path of the directory you want to list subdirectories for
'''
directory_path = SRC_DIR
subdirectories = list_subdirectories(directory_path)

print("Subdirectories in", directory_path, "are:")
for subdir in subdirectories:
    print(subdir)
'''

my_dirs = ['b432', 'b743', 'tc']

for d in my_dirs:
    s_dirs = list_subdirectories(f'{SRC_DIR}/{d}')
    print(s_dirs[0:10])
    start_time = time.time()
    move_directory( f'{SRC_DIR}/{d}', f'{DEST_DIR}/{d}')
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken to move the directory {d}: {elapsed_time} seconds")
