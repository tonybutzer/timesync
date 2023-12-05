import subprocess

def rerun(failed_out_file_name):
    print ('RETRY', failed_out_file_name)

    retry_str = failed_out_file_name.split('/')[-1]
    retry_str = retry_str.replace('.out', '')
    print(retry_str)
    (year, plot_id, project_id) = retry_str.split('_')
    print(year, plot_id, project_id)


# Define the command
command = "grep -L Success .out/*.out"

# Run the command and capture the output
result = subprocess.run(command, shell=True, text=True, capture_output=True)

# Check if the command was successful
if result.returncode == 0:
    # Print the output
    #print("Files without 'Success':")
    #print(result.stdout)
    pass
else:
    # Print the error message
    print("Error:", result.stderr)


lines = result.stdout.splitlines()

for line in lines:
    rerun(line)


