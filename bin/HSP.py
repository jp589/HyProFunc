#!/usr/bin/env python
import sys
import os
import pandas as pd

# Gets header-sequence pairs from a fasta file and writes the data to a CSV file.

# First positional argument is the filepath for the fasta file
# Second positional argument is the path to the intended output directory

def parse_fasta(fasta_file):
    with open(fasta_file, 'r') as file:
        header_sequence_pairs = []
        header = None
        sequence = []
        num_entries = 0

        for line in file:
            line = line.strip()
            if line.startswith(">"):
                if header:  # Save the previous entry before starting a new one
                    header_sequence_pairs.append((header, ''.join(sequence)))
                    num_entries += 1
                header = line[1:].split()[0]  # Extract header part after ">"
                sequence = []  # Reset sequence list for the new entry
            else:
                sequence.append(line)

        # Add the last entry after the loop ends
        if header:
            header_sequence_pairs.append((header, ''.join(sequence)))
            num_entries += 1

    return num_entries, header_sequence_pairs


# Parse the file and get the number of entries and header-sequence pairs
num_entries, header_sequence_pairs = parse_fasta(sys.argv[1])
print(num_entries)

csv_data = []
for pair in header_sequence_pairs:
    header = pair[0]
    sequence = pair[1]

    if len(sequence) > 400:
        sequence = sequence[:400]
    # Header sequence pairs stored as csv for easy retrieval later
    csv_data.append([header, sequence])


output_df = pd.DataFrame(csv_data, columns=['Header', 'Sequence'])
output_csv = sys.argv[2] + 'Header_Sequence.csv'
file_exists = os.path.isfile(output_csv)
output_df.to_csv(output_csv, index=False, mode='a', header=not file_exists)
