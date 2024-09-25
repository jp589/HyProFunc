#!/usr/bin/env python

import sys
import pandas as pd

# Load the two CSV files
# first positional argument is annotated protein functions
# second positional argument is the determined protein functions
file1 = sys.argv[1]
file2 = sys.argv[2]

# Read the CSV files into DataFrames
df1 = pd.read_csv(file1)
#drops the redundant sequence column
df1 = df1.drop(df1.columns[2], axis=1)
df2 = pd.read_csv(file2)

# Perform a right join based on the first column of both files
# Assuming the first column is named the same in both files
merged_df = pd.merge(df1, df2, left_on=df1.columns[0], right_on=df2.columns[0], how='right')

# remove duplicate rows based on the header
merged_df = merged_df.drop_duplicates(subset='Header')

# Save the merged DataFrame to a new CSV file
output_file = sys.argv[3] + 'Merged_Protein_Functions.csv'
merged_df.to_csv(output_file, index=False)

print(f'Comparison saved to {output_file}')
