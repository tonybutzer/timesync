#!/usr/bin/env python
# coding: utf-8


import sys

# Check if at least one argument is provided
if len(sys.argv) < 2:
    print("Usage: python script.py <year>")
    sys.exit(1)

# Fetch the first argument and assign it to the variable my_year
my_year = int(sys.argv[1])

# Now you can use my_year in your script
print("The year is:", my_year)



#! ls /efs/timesync/1984/audit
from tqdm import tqdm


import os

def list_files_in_directory(directory):
    try:
        # Get the list of files in the specified directory
        files = os.listdir(directory)

        # Print or return the list of files
        return files

    except OSError as e:
        print(f"Error reading directory {directory}: {e}")
        return []



# Print the list of files
#print(files_in_directory)


# directory_path = f"/efs/timesync/{my_year}/audit"

tall_path = f'/caldera/projects/usgs/water/impd/butzer/timesync/{my_year}/audit'
directory_path = tall_path


orig_path = '/efs/'
tall_replace = '/caldera/projects/usgs/water/impd/butzer/'

# Call the function with the specified directory path
files_in_directory = list_files_in_directory(directory_path)


files_in_directory[:10]


import pickle

def unpickle_object(file_path):
    try:
        with open(file_path, 'rb') as file:
            # Unpickle the object from the file
            unpickled_object = pickle.load(file)
            return unpickled_object

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

    except Exception as e:
        print(f"Error unpickling object: {e}")
        return None



import os

def verify_csv_file(file_path):
    file_path = file_path.replace(orig_path, tall_replace)
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        # Check if the file has a ".csv" extension
        if not file_path.lower().endswith(".csv"):
            print(f"File does not have a .csv extension: {file_path}")
            return False

        # If both conditions are met, return True
        return True

    except Exception as e:
        print(f"Error verifying file: {e}")
        return False

def verify_png_file(file_path):
    file_path = file_path.replace(orig_path, tall_replace)
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        # Check if the file has a ".csv" extension
        if not file_path.lower().endswith(".png"):
            print(f"File does not have a .png extension: {file_path}")
            return False

        # If both conditions are met, return True
        return True

    except Exception as e:
        print(f"Error verifying file: {e}")
        return False


def verify_validate(d):
    #print(type(d))
    cnt = 0
    for i in d:
        f = i['scsv']
        verify_csv_file(f)
        ftc = i['tcap']
        verify_png_file(ftc)
        fb432 = i['b432']
        verify_png_file(fb432)
        fb743 = i['b432']
        verify_png_file(fb743)
        #validate(f)
        # print(cnt, end=' ', flush=True)
        cnt = cnt + 1


for i in tqdm(range(0,len(files_in_directory))):
    p_file = files_in_directory[i]
    full_p_file = f'{directory_path}/{p_file}'
    my_file_dict = unpickle_object(full_p_file)
    verify_validate(my_file_dict)




