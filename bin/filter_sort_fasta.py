#!/usr/bin/env python

from Bio import SeqIO
import sys

def filter_and_sort_fasta(input_fasta, output_fasta, min_length):
    # Parse the input fasta file and filter sequences by length
    sequences = [record for record in SeqIO.parse(input_fasta, "fasta") if len(record.seq) >= min_length]
    
    # Sort sequences by length in descending order
    sorted_sequences = sorted(sequences, key=lambda x: len(x.seq), reverse=True)
    
    # Write the filtered and sorted sequences to a new fasta file
    with open(output_fasta, "w") as output_handle:
        SeqIO.write(sorted_sequences, output_handle, "fasta")
    
    print(f"Filtered {len(sorted_sequences)} sequences and saved to {output_fasta}.")

input_fasta = sys.argv[1]
output_fasta = sys.argv[2]
min_length = int(sys.argv[3])

filter_and_sort_fasta(input_fasta, output_fasta, min_length)

