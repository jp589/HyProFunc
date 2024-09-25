#!/usr/bin/env python

import requests
import ssl
import sys
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.poolmanager import PoolManager
import os
import pandas as pd
import fnmatch

# ESMFold has known SSL certificate issues. Due to SAN mismatch in current certificate
# a custom SSL context was created to disable hostname verification and bypass certificate validation
# while maintaining SSL encryption for data transfer.
# Archived thread documenting SSL certificate issues with ESMFold:
# https://github.com/facebookresearch/esm/discussions/627

class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)

# Creates a custom SSL context
context = ssl.create_default_context()
pem_file_path = sys.argv[3] # File path for the .pem file
context.load_verify_locations(pem_file_path) # Loads the .pem file
context.check_hostname = False  # Disable hostname verification
context.verify_mode = ssl.CERT_NONE  # Bypass certificate validation

# Use the custom SSL context in a session
session = requests.Session()
session.mount('https://', SSLAdapter(ssl_context=context))

# Function defintion for a function that parses the fasta file.
# Assumes that a unique sequence identifier (USI) follows the `>` in the fasta header for each sequence.
# If the USI contains spaces, this will only keep the first segment:
# For example if the header line is `>sequence 1` this function will only retain `sequence`
# Rather, the header line should be formatted as `>sequence_1`
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
                header = line[1:].replace('|','_').replace('(','-').replace(')','-').split()[0]  # Extract header part after ">"
                sequence = []  # Reset sequence list for the new entry
            else:
                sequence.append(line.replace(' ', ''))

        # Add the last entry after the loop ends
        if header:
            header_sequence_pairs.append((header, ''.join(sequence)))
            num_entries += 1

    return num_entries, header_sequence_pairs


# Function to check if the USI in the header already has an associated `.pdb` file.
def header_not_in_filename(header, dir):
    for root, dirs, files in os.walk(dir):
        for filename in fnmatch.filter(files, '*.pdb'):
            if header in filename:
                return False
    return True


# Parse the file and get the number of entries and header-sequence pairs
num_entries, header_sequence_pairs = parse_fasta(sys.argv[1])

print(f"{num_entries} total entries observed in the fasta file.")

with open(sys.argv[2] + 'num_entries', 'w') as f:
        f.write(str(num_entries))

csv_data = []
# API URL for ESMFold
url = "https://api.esmatlas.com/foldSequence/v1/pdb/"

sequences_processed = 0

for pair in header_sequence_pairs:
    header = pair[0]
    sequence = pair[1]

    # Checks to see if .pdb is already created
    if header_not_in_filename(header,sys.argv[2]):
        if sequences_processed == 50:
            print("Limit of 50 ESMFold API requests reached")
            break
        # ESMFold limits query sequences to 400 amino acids.
        if len(sequence) > 400:
            print(f"Sequence {header} trimmed to 400 amino acids.")
            sequence = sequence[:400]

        # Header sequence pairs stored as csv for easy retrieval later.
        csv_data.append([header, sequence])
        #output_df = pd.DataFrame(csv_data, columns=['Header', 'Sequence'])
        #output_csv = sys.argv[2] + 'Header_Sequence.csv'
        #file_exists = os.path.isfile(output_csv)
        #output_df.to_csv(output_csv, index=False, mode='a', header=not file_exists)

        # Previous iteration utilized unverfied connection.
        # response = post(url, data=sequence, verify=False)
        # Assuming the SSL certification issue is resolved, remove `session.` from the following line
        response = session.post(url, data=sequence)
        with open(sys.argv[2] + header + '.pdb', 'wb') as outfile:
            outfile.write(response.content)
        print(f"Processed sequence: {header}")
        sequences_processed += 1
    else:
        print(f"{header}.pdb already present in {sys.argv[2]}. Skipping ESMFold.")


output_csv = sys.argv[2] + 'Header_Sequence.csv'
file_exists = os.path.isfile(output_csv)

if file_exists:
    with open(output_csv, 'r') as file:
        lines = file.readlines()[1:]
        current_length = len(lines)
    if current_length == num_entries:
        print(f"All sequences already represented in {output_csv}")
    elif current_length > num_entries:
        print(f"Current number of entries in {output_csv} is {current_length}. Something went wrong")
    else:
        print(f"Adding {len(csv_data)} header sequence pairs to {output_csv}")
        output_df = pd.DataFrame(csv_data, columns=['Header', 'Sequence'])
        output_df.to_csv(output_csv, index=False, mode='a', header=not file_exists)

else:
     print(f"Adding {len(csv_data)} header sequence pairs to {output_csv}")
     output_df = pd.DataFrame(csv_data, columns=['Header', 'Sequence'])
     output_df.to_csv(output_csv, index=False, mode='a', header=not file_exists)
