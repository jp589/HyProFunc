#!/usr/bin/env python
import sys

def remove_duplicates_fasta(input_file, output_file):
    # Dictionary to store unique sequences
    unique_sequences = {}
    
    with open(input_file, 'r') as infile:
        header = None
        sequence = []
        
        for line in infile:
            line = line.strip()
            
            if line.startswith('>'):  # It's a header line
                # If there's a previous sequence, check if it's unique
                if header and ''.join(sequence) not in unique_sequences.values():
                    unique_sequences[header] = ''.join(sequence)
                
                # Start a new sequence
                header = line
                sequence = []
            
            else:
                # It's part of the sequence, so add to the current sequence
                sequence.append(line)
        
        # Add the last sequence to the dictionary if unique
        if header and ''.join(sequence) not in unique_sequences.values():
            unique_sequences[header] = ''.join(sequence)
    
    # Write unique sequences to the output file
    with open(output_file, 'w') as outfile:
        for header, seq in unique_sequences.items():
            outfile.write(f"{header}\n")
            # Write the sequence in 80 character chunks for proper FASTA format
            for i in range(0, len(seq), 80):
                outfile.write(seq[i:i+80] + '\n')

# first positional argument is the original fasta file.
# second positional argument is the file path to the output file
remove_duplicates_fasta(sys.argv[1], sys.argv[2])
