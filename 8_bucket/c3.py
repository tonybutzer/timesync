import fsspec
import s3fs

def count_files_with_extension(files, extension):
    return sum(1 for file in files if file.endswith(extension))

def list_files_recursively_s3(bucket_name, prefix=''):
    s3_url = f's3://{bucket_name}/{prefix}'
    fs = s3fs.S3FileSystem(anon=False)
    # fs = fsspec.filesystem(s3_url)
    
    files = []
    for root, dirs, filenames in fs.walk(s3_url):
        for fn in filenames:
            files.append(fn)
    return files

# Replace 'your-bucket-name' with the name of your S3 bucket
# Replace 'your-prefix' with the prefix you want to start listing from
bucket_name = 'dev-nlcd-developer'
prefix = 'timesync/1995'  # You can specify a prefix if needed

files = list_files_recursively_s3(bucket_name, prefix)

# Display the list of files
csv_count = count_files_with_extension(files, '.csv')
png_count = count_files_with_extension(files, '.png')

print(f"Number of .csv files: {csv_count}")
print(f"Number of .png files: {png_count}")

