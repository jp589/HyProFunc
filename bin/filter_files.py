#!/usr/bin/env python

import os
import glob
import sys

# Extract the first column (excluding header) from the CSV file
def get_first_column_values(csv_file):
    values = set()
    with open(csv_file, 'r') as f:
        next(f)  # Skip the header
        for line in f:
            values.add(line.split(',')[0].strip())
    return values

# Remove files containing these values from the list of files
def filter_files(values, pattern):
    all_files = glob.glob(pattern)
    files_to_process = []
    
    for file_path in all_files:
        file_name = os.path.basename(file_path)
        # Check if any value from the first column is in the file name
        if not any(value in file_name for value in values):
            files_to_process.append(file_path)
    
    return files_to_process

# Example usage
csv_file = sys.argv[1]

dir = sys.argv[2]
#file_pattern = './Select_*.csv'
file_pattern = sys.argv[3]

# Get values from the first column
values = get_first_column_values(csv_file)

if 'print_values' in sys.argv:
    print("Sequence IDs already determined:")
    for value in values:
        print(value)
    sys.exit(0)

# Filter files based on the extracted values
files_to_process = filter_files(values, dir + file_pattern)

# Print each file path on a new line (Bash-friendly)
for file in files_to_process:
    print(file)
