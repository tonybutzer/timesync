#!/usr/bin/env python
# coding: utf-8

import fsspec
import s3fs

def count_files_with_extension(files, extension):
    return sum(1 for file in files if file.endswith(extension))

def list_bucket_contents(bucket_name, prefix=''):
    fs = s3fs.S3FileSystem(anon=False)
    files = fs.ls(f'{bucket_name}/{prefix}', detail=False)
    #files = fs.ls(f'{bucket_name}/{prefix}', detail=True)

    #csv_count = count_files_with_extension(files, '.csv')
    #png_count = count_files_with_extension(files, '.png')

    #print(f"Number of .csv files: {csv_count}")
    #print(f"Number of .png files: {png_count}")
    
    print("\nPrefixes:")
    prefixes = set()
    for file in files:
        print(file)
        # Extracting the prefix from the file path
        parts = file[len(f'{bucket_name}/{prefix}'):].split('/')
        if len(parts) > 1:
            prefixes.add(parts[0])

    print("\n".join(prefixes))

# Replace 'your-bucket-name' with your actual bucket name
list_bucket_contents('dev-nlcd-developer', 'timesync')

