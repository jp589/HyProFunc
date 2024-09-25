#!/usr/bin/env python

import random
import sys
import os
from Bio import SeqIO

# Input and output file paths
# Input gbff
input_file = sys.argv[1]
if not input_file.endswith('.gbff'):
    print(f"{sys.argv[1]} is not a .gbff file.")
    sys.exit(0)

# Function to optionally set the seed
def get_seed(user_seed=None):
    if user_seed is not None:
        random.seed(user_seed)
        return user_seed
    else:
        seed = random.randint(0, 2**32 - 1)  # Generate a random seed
        random.seed(seed)
        return seed

# Parse the GenBank file and extract amino acid sequences (protein-coding)
sequences = []
for record in SeqIO.parse(input_file, "genbank"):
    organism = record.annotations.get("organism", "Unknown organism").replace(" ", "_")

    # Iterate over features to find CDS (protein-coding sequences)
    for feature in record.features:
        if feature.type == "CDS" and "translation" in feature.qualifiers:
            locus_tag = feature.qualifiers.get("locus_tag", ["Unknown_locus_tag"])[0]
            product = feature.qualifiers.get("product", ["Unknown_product"])[0]
            sequence = feature.qualifiers["translation"][0]

            # Build the FASTA header with the desired fields
            header = f">{locus_tag} {organism} {product}"
            sequences.append((header, sequence))

# Ask for seed input (optional)
user_seed = input("Enter seed for random sequence selection or press enter to generate one randomly: ")

seed = get_seed(int(user_seed) if user_seed else None)
print(f"Using seed: {seed}")

# Select random sequences - 10 by default
random_sequences = random.sample(sequences, min(int(sys.argv[2]), len(sequences)))

# output fasta (.faa)
output_file = os.path.basename(input_file).replace('.gbff', '_random_seqs') + "_seed" + str(seed) + ".faa"

# Write the selected sequences to a FASTA file
with open(output_file, "w") as fasta_out:
    for header, seq in random_sequences:
        fasta_out.write(f"{header}\n")
        # Split sequence into lines of 60 characters (FASTA format standard)
        for i in range(0, len(seq), 60):
            fasta_out.write(f"{seq[i:i+60]}\n")

print(f"{sys.argv[2]} amino acid sequences written to {output_file}")
