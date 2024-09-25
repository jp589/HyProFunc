#!/usr/bin/env python

import pandas as pd
from collections import Counter
import itertools
import sys
import os
import subprocess

# this is the tab-separated concatenated table from the Foldseek API request
input_tsv = sys.argv[1]

if not os.path.exists(input_tsv):
    print(f"File {input_tsv} doesn't exist.")
    sys.exit(0)


Head_ID = os.path.basename(input_tsv).replace('.tsv','')

# Check if the file is empty
if os.path.getsize(input_tsv) == 0:
    Indicator_file = os.path.join(os.path.dirname(input_tsv), Head_ID + "_empty")
    print(f"The file is empty. Creating indicator file {Indicator_file}")
    with open(Indicator_file, 'a'):
        pass
    sys.exit(0)

# Load the TSV file
df = pd.read_csv(input_tsv, sep='\t', header=None)
# We only need to retain three columns from this table
df = df[[1,2,10]]
df.columns = ['description','SeqID', 'prob']

# Creates an indicator file if there are no entries with a probablity of 1
if len(df[df['prob'] == 1]) == 0:
    Indicator_file = os.path.join(os.path.dirname(input_tsv), Head_ID + "_no_prob_one")
    print(f"No entries with probability equal to one. Creating indicator file {Indicator_file}")
    with open(Indicator_file, 'a'):
        pass
    sys.exit(0)

# Filters table to entries with probability of 1
df = df[df['prob'] == 1]

# Removes non-informative substrings from entries in the description column.
df['description'] = df['description'].str.replace(r'AF.*-F1-model_v4 ', '', case=False, regex=True)
df = df[df['description'] != 'Uncharacterized protein']
df = df[df['description'] != 'Uncharacterized']
df['description'] = df['description'].str.replace('uncharacterized', '', case=False, regex=False)
df['description'] = df['description'].str.replace(' protein', '', case=False, regex=False)
df['description'] = df['description'].str.replace('putative', '', case=False, regex=False)
df['description'] = df['description'].str.replace('domain-containing', '', case=False, regex=False)
df = df[df['description'].str.lower() != 'na']

# Extract the description column and drop any missing values
descriptions = df['description'].dropna().str.strip()
descriptions = descriptions[descriptions != '']
descriptions = descriptions[descriptions != ' ']
descriptions = descriptions.tolist()

# Get the total number of rows
total_rows = len(df)
# creates indicator file if there are no informative entries remaining
if total_rows == 0:
    Indicator_file = os.path.join(os.path.dirname(input_tsv), Head_ID + "_no_info")
    print(f"No entries with informative descriptions. Creating indicator file {Indicator_file}")
    with open(Indicator_file, 'a'):
        pass
    sys.exit(0)

# Function to generate substrings of a specific length
def generate_substrings_of_length(text, length):
    substrings = [text[i:i + length] for i in range(len(text) - length + 1)]
    return substrings

csv_data = []
longest_substring_above_50 = None

# Loop through each substring length within the following range
for length in range(3, 60):
    # Flatten the list of all substrings of the current length from all descriptions
    all_substrings = list(itertools.chain.from_iterable(generate_substrings_of_length(desc, length) for desc in descriptions))

    # Count the occurrences of each substring
    substring_counts = Counter(all_substrings)

    # Find the most common substring of this length
    if substring_counts:
        most_common_substring, count = substring_counts.most_common(1)[0]

        # Calculate the percentage of rows that contain the most common substring
        rows_with_substring = sum(1 for desc in descriptions if most_common_substring in desc)
        percentage = (rows_with_substring / total_rows) * 100

        # Store the data for the CSV file
        csv_data.append([length, most_common_substring, count, percentage])
        # Update the longest substring with percentage > 50%
        if percentage > 50:
            longest_substring_above_50 = (most_common_substring, length, percentage)

# Write the data to a new CSV file
output_df = pd.DataFrame(csv_data, columns=['substring_length', 'substring', 'count', 'percentage'])
output_csv = os.path.join(
    os.path.dirname(input_tsv),
    "substrings_" + os.path.basename(input_tsv).replace('.tsv', '.csv')
)
output_df.to_csv(output_csv, index=False)

# Write descriptions to new CSV file
df_out = os.path.join(
os.path.dirname(input_tsv), "Select_" + os.path.basename(input_tsv).replace('.tsv','.csv'))
df.to_csv(df_out, index=False)
