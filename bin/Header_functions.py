#!/usr/bin/env python
import sys
import os
import pandas as pd
import re

# Extracts header ID and annotated function from a fasta header.
# First positional argument is the filepath to the fasta file.
# Second positional argument is the path for the intended output directory
# Third positional argument is optional word (characters separated by whitespace) number of annotated function
# or regex pattern to extract function.

# By default this script assumes that a header would be in the format:
# >[HEADER_ID] [Bacterial_Strain_Name] [Function]
# For example:
# >ABC12_1234   Escherichia_coli_K12   ABC transporter permease
# Here, everything from the third word 'ABC' on is assumed to be the functional annotation.

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
                    header_sequence_pairs.append((header, ''.join(sequence), ' '.join(function)))
                    num_entries += 1
                header = line[1:].replace('|', '_').replace('(', '-').replace(')', '-').split()[0]  # Extract header part after ">"
                if len(sys.argv) > 3:
                    try:
                        int_val = int(sys.argv[3]) - 1
                        function = line[1:].replace('|', '_').replace('(', '-').replace(')', '-').split()[int_val]
                    except:
                        match = re.search(sys.argv[3], line[1:].replace('|','_').replace('(','-').replace(')','-'))
                        function = match.group(1)
                else:
                    function = line[1:].replace('|', '_').replace('(', '-').replace(')', '-').split()[2:]
                sequence = []  # Reset sequence list for the new entry
            else:
                sequence.append(line)

        # Add the last entry after the loop ends
        if header:
            header_sequence_pairs.append((header, ''.join(sequence), ' '.join(function)))
            num_entries += 1

    return num_entries, header_sequence_pairs


# Parse the file and get the number of entries and header-sequence pairs
num_entries, header_sequence_pairs = parse_fasta(sys.argv[1])
print(f"{num_entries} entries observed in the fasta file {sys.argv[1]}")

csv_data = []
for pair in header_sequence_pairs:
    #print(pair)
    header = pair[0]
    sequence = pair[1]
    function = pair[2]
    # Header sequence pairs stored as csv for easy retrieval later
    csv_data.append([header, function, sequence])


output_df = pd.DataFrame(csv_data, columns=['Header','Function', 'Sequence'])
output_csv = sys.argv[2] + 'Original_Header_Function.csv'
file_exists = os.path.isfile(output_csv)
output_df.to_csv(output_csv, index=False, mode='a', header=not file_exists, encoding="utf-8")
print(f"{output_csv} created.")
