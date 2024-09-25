#!/usr/bin/env python

import pandas as pd
from collections import Counter
import itertools
import sys
import os
import subprocess
import csv

# File path to the descriptions table with only select columns.
input_csv = sys.argv[1]
input_csv = input_csv.strip()
input_csv = os.path.normpath(input_csv)
# Check if the file is empty.
# This might happen if no target proteins have a probabilty = 1.
if os.path.getsize(input_csv) == 0:
    print("The file is empty.")
    sys.exit(0)

# Load the column-selected descriptions CSV file into a pandas dataframe
df = pd.read_csv(input_csv, header=0)

# last removal of blank rows
df = df.dropna()

total_rows = len(df) # gets the total number of rows


# We don't want duplicate entries so we check if the file exists and if so, is there already a matching entry.

# Check if the file exists
pf_path = os.path.join(os.path.dirname(input_csv),"Protein_functions.csv")
Head_ID = os.path.basename(input_csv).replace('Select_','').replace('.csv','')

if os.path.exists(pf_path):
    pf = pd.read_csv(pf_path, header=0)
    # Checks if the protein function has already been inferred.
    if pf['Input_Sequence_Identifier'].isin([Head_ID]).any():
        print(f"Protein function for {Head_ID} already determined.")
        sys.exit(1)

# Loads the substring CSV file
csv_data = []
with open(os.path.join(os.path.dirname(input_csv), os.path.basename(input_csv).replace('Select_', 'substrings_')), 'r') as file:
    reader = csv.reader(file)
    next(reader) # skips the first row
    for row in reader:
        row[0] = float(row[0])
        row[2] = float(row[2])
        row[3] = float(row[3])
        csv_data.append(row)
output_df = pd.DataFrame(csv_data, columns=['substring_length', 'substring', 'count', 'percentage'])


def calculate_overlap(substr1, substr2):
    """Calculate the maximum number of sequential overlapping characters."""
    max_overlap = 0
    len1, len2 = len(substr1), len(substr2)

    # Check if substr1 is contained within substr2
    if substr1 in substr2:
        return len(substr1)

    # Check all possible positions of substr2 within substr1
    for start in range(len2):
        overlap_length = 0
        while (start + overlap_length < len2) and (overlap_length < len1) and (substr1[overlap_length] == substr2[start + overlap_length]):
            overlap_length += 1
        max_overlap = max(max_overlap, overlap_length)

    return max_overlap

# instantiates with starting values.
max_overlap = 0
best_pair = None
max_score = 0

# Iterate through all pairs of substrings to determine overlap, percentage of entries containing substring
# and the average SeqID for entries containing the substring.
# We pair all substrings together to find the best pair and report the longest of the pair.

# Overlap between the two substrings helps to detect when multiple substrings are keying in on the same
# definition substring - if substring_1 is `otease` and substring_2 is `protease` we would observe
# a high degree of overlap suggesting that the protein is indeed likely a `protease`.

# To determine a specific substring score we weight the average SeqID by the fourth root of the length
# times the percentage of entries with the substring divided by the percentage of entries with the next
# longest substring.

# Finally, we ignore any substrings that are not found in at least 10% of the entries returned by Foldseek.

for i in range(len(csv_data) - 1):
    substring_1 = csv_data[i][1]
    length_1 = csv_data[i][0]

    for j in range(i + 1, len(csv_data)):
        substring_2 = csv_data[j][1]
        length_2 = csv_data[j][0]
        if j < len(csv_data)-1:
            substring_3 = csv_data[j+1][1]
            # calculates percentage of rows with substring_3
            pct_count_substr3 = df['description'].str.contains(substring_3, regex=False).sum() / total_rows
        else:
            # by setting this to 1 we ignore it.
            pct_count_substr3 = 1

        overlap = calculate_overlap(substring_1, substring_2) # calculates overlap

        # Calculate percentage of rows with substring_2
        pct_entry_count = df['description'].str.contains(substring_2, regex=False).sum() / total_rows

        # Calculate average SeqID for rows containing substring_2
        avg_SeqID = df[df['description'].str.contains(substring_2, regex=False)]['SeqID'].mean()
        # determines weight to be applied to the average SeqID
        weight = (length_2**0.25)*pct_entry_count/pct_count_substr3
        #debug print statement
        #print(f"Substring 1:{substring_1}, Substring 2:{substring_2}, avg_SeqID*weight=score: {avg_SeqID}*{weight}={avg_SeqID*weight} and pct_entry_count {pct_entry_count}%\n")

        # Update best_pair if this is the best overlap found so far
        if overlap > max_overlap and (weight*avg_SeqID > max_score) and (pct_entry_count > 0.10):
            max_overlap = overlap
            max_score = weight*avg_SeqID
            best_pair = (substring_1, substring_2)
            #debug print statement
            #print(f"best pair: {best_pair[0]},{best_pair[1]}, max_score: {max_score}\n")

# Print the longest substring with the highest degree of overlap
if best_pair:
    print(f"The most likely protein based on predicted structure was: '{best_pair[1]}' with a percent entry count (for prob=1): {output_df[output_df['substring'] == best_pair[1]]['percentage'].iloc[0]:.2f}%, and mean SeqID of: {avg_SeqID:.2f}")
    Head_ID = os.path.basename(input_csv).replace('Select_','').replace('.csv', '')
    longest_substring = best_pair[1]
    percent_entry_count = output_df[output_df['substring'] == best_pair[1]]['percentage'].iloc[0]
    mean_seq_id = avg_SeqID

    sequence_data = pd.read_csv(os.path.dirname(input_csv) + '/Header_Sequence.csv')
    AA_sequence =  sequence_data.loc[sequence_data['Header'] == Head_ID, 'Sequence'].values

    # Create a dictionary with the data
    data = {
        # Header of the input amino acid sequence
        'Input_Sequence_Identifier': [Head_ID],
        # Best guess of protein function based on structure-based comparison
        'Inferred_Protein_Function': [longest_substring],
        # Percent of entries with probability = 1 that contain the substring
        'Percent_Entry_Count': [f'{percent_entry_count:.2f}'],
        # Average SeqID score of entries containing the substring
        'Mean_SeqID': [f'{mean_seq_id:.2f}'],
        # Processed amino acid sequence
        'Amino_acid_sequence': [AA_sequence[0]]
    }
    # Convert to DataFrame
    df = pd.DataFrame(data)
    # Define the output file name
    output_file = 'Protein_Functions.csv'

    # Check if the file exists
    if os.path.exists(os.path.join(os.path.dirname(input_csv),output_file)):
        # Append to the file without writing the header
        df.to_csv(os.path.join(os.path.dirname(input_csv),output_file), mode='a', header=False, index=False)
    else:
        # Write to the file with the header
        df.to_csv(os.path.join(os.path.dirname(input_csv),output_file), mode='w', header=True, index=False)
        print(f"Results written to: {os.path.join(os.path.dirname(input_csv),output_file)}")
