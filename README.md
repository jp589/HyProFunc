# HyProFunc - Hypothetical Protein Function determination based on predicted structure  

## Description

Roughly speaking, HyProFunc is a computationally light script (for the user) that utilizes the APIs of ESMFold (https://esmatlas.com/about#api ; https://www.science.org/doi/abs/10.1126/science.ade2574) and Foldseek (https://search.foldseek.com/search ; https://github.com/steineggerlab/foldseek)
to predict protein structure and subsequently predict function from a given amino acid sequence provided in fasta format (https://en.wikipedia.org/wiki/FASTA_format).

While HyProFunc is quite good at predicting protein function, it is not intended to replace current annotation pipelines such as PROKKA, PGAP, etc. Instead, it is intended to supplement the annotation of genomes where standard annotation fails. Namely, to infer protein function of so-called hypothetical proteins. HyProFunc works on the principle that, regardless of amino acid sequence, proteins with similar structures share similar functions. This hypothetical protein function inference is especially needed for the rapidly increasing number of poorly-studied bacterial genomes.

**WARNING:** Because of HyProFunc's sole reliance on predicted protein structure to determine function, if multiple proteins share a similar protein structure but ultimately perform different functions, this can lead to ambiguous or incorrect determinations of protein function.

Also, keep in mind that HyProFunc is still in the early stages of development.

### HyProFunc steps to determine protein function (for each amino acid sequence provided in a given .fasta file)
1. Submit amino acid sequence to ESMFold (up to 400 amino acids long).
    - Successful submission returns a protein structure in `.pdb` format.
2. Submit the `.pdb` structure to Foldseek.
    - Foldseek compares the structure to three Alphafold databases.
	    - AFDB50, AFDB-SWISSPROT, AFDB-PROTEOME
    - Successful submission returns tabular results in `.m8` format.
3. Strip the tabular results of extraneous information.
4. Parse the best structure-matching descriptions for common substrings.
    - Returns
       a. original header ID
       b. percentage of descriptions containing the substring
       c. the average SeqID of all matches containing the substring
       d. the sequence submitted to ESMFold.
5. Optional comparison to original annotation contained in the fasta header.
    - Returns a merged table to compare inferred function to original annotation.

## Installation:

Installation is simple:

1. Download the Github repository to your current working directory.
	a. If you have git bash you can simply run:
		`$ git clone https://github.com/jp589/HyProFunc
	b. Alternative download and extraction    
		`$ wget https://github.com/jp589/HyProFunc/archive/refs/heads/master.zip
	    `$ unzip -j master.zip
	    `$ rm master.zip
2. Add the directory containing the `HyProFunc.sh` script to your path.
	a. Temporarily add HyProFunc to path for each session. 
		`export PATH="path/to/HyProFunc:$PATH"
	b. Modify PATH environment variable in system settings for permanent addition.
3. For parsing of `.gbff` files install Biopython (Optional).
		`pip install biopython`
		See https://biopython.org/wiki/Download for more details.
4. Test with example data:
		`$ cp /your/script/location/data/Example_data.fa .`
		`$ Hypothetical_Protein_Function.sh -c -f Example_data.fa`
## Usage:
    HyProFunc.sh [-h] [-c] [-e] [-r] [-g genome.gbff] [-f fasta.faa] [-p 3]

-h  Displays help page.
-c  Optional flag to compare protein function annotation in header sequence to this script's output.
-e  Optional flag to extract amino acid sequences denoted as hypothetical in the fasta header.
-g  Optional .gbff file from which amino acid sequences will randomly be extracted and compared to this script's output.
-r  Optional flag to remove duplicate fasta entries.
-f  Fasta file containing amino acid sequences.
-p Optional word number (character string separated by whitespace) or regex pattern to match annotated function in fasta header. Default behavior is to extract all characters after the second whitespace. This is only needed when comparing functional annotation in the header sequence to this script's output. Example generic regex pattern: `'r">.*(.*).*\s"'

Header sequence IDs are determined by default as the characters immediately following the '>' until the first whitespace.

These IDs will be used for intermediate file naming so try to avoid special characters.
However, `'|'`, `'('`, and `')'` will be converted to `'_'` before Header sequence ID extraction if present.


This script determines protein function based on the amino acid sequences provided in a fasta format.

If the '-c' option is used with '-g', only the fasta file derived from the .gbff file will be used for protein function determination.

**Keep in mind that the Biopython module is required to parse the .gbff file if included.**

Each sequence is trimmed to the first 400 amino acids and then submitted to the ESMFold API:
    "https://api.esmatlas.com/foldSequence/v1/pdb/"
The subsequently generated .pdb file is sumbitted to the Foldseek API:
    "https://search.foldseek.com/api/ticket"
as a query against three Alphafold databases: AFDB50, AFDB-SWISSPROT, AFDB-PROTEOME.
This results in a table of structurally similar proteins.
The descriptions are parsed to determine the most common substring.
This substring is reported along with the header, percentage of descriptions containing the substring, the average SeqID, and the sequence submitted to ESMFold.

Please keep in mind that this script utilizes APIs that are considered shared resources.
As such, the ESMFold API is limited to 50 requests at a time,
and the Foldseek API request loop will break after the rate limit has been reached.

Please also note that the ESMFold API has known SSL certificate issues:
    "https://github.com/facebookresearch/esm/discussions/627"

This script makes use of a custom SSL connection that disables hostname verification and bypasses
certificate validation, but SSL encryption is maintained for data transfer.
