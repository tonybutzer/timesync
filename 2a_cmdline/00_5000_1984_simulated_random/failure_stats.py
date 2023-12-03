import os
import pandas as pd

f_list=[]

# Set the path to your directory containing *.out files
directory_path = ".out"

# Get a list of all *.out files in the directory
files_list = [f for f in os.listdir(directory_path) if f.endswith('.out')]

# Create a pandas DataFrame to store the results
#result_df = pd.DataFrame(columns=['File', 'Failure_Count'])

# Loop through each file and count the occurrences of "Failure"
for file_name in files_list:
    file_path = os.path.join(directory_path, file_name)
    
    with open(file_path, 'r') as file:
        content = file.read()
        failure_count = content.count('Failed')
        print({'File': file_name, 'Failure_Count': failure_count})
        
        # Append the results to the DataFrame
        f_list.append({'File': file_name, 'Failure_Count': failure_count})

result_df = pd.DataFrame(f_list)
# Print the resulting DataFrame
print(result_df)

print(result_df.describe())

#print(result_df.hist())


def create_text_histogram(data):
    histogram = {}
    
    # Count the occurrences of each value
    for value in data:
        histogram[value] = histogram.get(value, 0) + 1
    
    # Print the text histogram
    for key, value in histogram.items():
        print(f'{key}: {"#" * value}')

# Example usage:
#data_list = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]

data_list = result_df['Failure_Count'].to_list()

create_text_histogram(data_list)

# Optional: Save the DataFrame to a CSV file
result_df.to_csv('failure_counts.csv', index=False)


