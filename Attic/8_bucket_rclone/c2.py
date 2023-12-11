#!/usr/bin/env python
# coding: utf-8

import fsspec
import s3fs

def list_files_recursively(fs, path):
    files = []
    for root, dirs, filenames in fs.walk(path):
        for filename in filenames:
            files.append(fsspec.filesystem.PathManager.join(root, filename))
    return files

# Replace 'your-filesystem-url' with the actual URL of your file system (e.g., 's3://your-bucket-name')
def list_bucket_contents(bucket_name, prefix=''):
    fs = s3fs.S3FileSystem(anon=False)
    path = f's3://{bucket_name}/{prefix}'


files = list_files_recursively(fs, path)

# Display the list of files
print(files)

