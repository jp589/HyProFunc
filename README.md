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
    - Returns:  
       a. original header ID  
       b. percentage of descriptions containing the substring  
       c. the average SeqID of all matches containing the substring  
       d. the sequence submitted to ESMFold.  
6. Optional comparison to original annotation contained in the fasta header.
    - Returns a merged table to compare inferred function to original annotation.

## Installation:

Installation is simple:

1. Download the Github repository to your current working directory.  
	a. If you have git bash you can simply run:  
		`$ git clone https://github.com/jp589/HyProFunc`  
	b. Alternative download and extraction    
		`$ wget https://github.com/jp589/HyProFunc/archive/refs/heads/master.zip`  
	    `$ unzip -j master.zip`  
	    `$ rm master.zip`  
2. Add the directory containing the `HyProFunc.sh` script to your path.  
	a. Temporarily add HyProFunc to path for each session.   
		    `export PATH="path/to/HyProFunc:$PATH"`   
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
-g  Optional .gbff or .gbk file from which amino acid sequences will randomly be extracted and compared to this script's output.  
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

## Example Use Cases

You're new to HyProFunc, you have a genome in .gbff format and want to see what it can do. 
The following line of code will extract amino acid sequences and compare the previously annotated function to the HyProFunc inferred function.

`HyProFunc.sh -c -g genome.gbff`

You have extracted a subset of amino acid sequences yourself and want to compare previous annotation to inferred function.

`HyProFunc.sh -c -f fasta.faa`

You are only interested in the amino acid sequences annotated as "hypothetical"

`HyProFunc.sh -e -f fasta.faa`

Your fasta file contains duplicate entries and you want to remove the duplicates before processing.

`HyProFunc.sh -r -f fasta.faa`

You're comparing annotated function to inferred function, but the annotated function is not everything that follows after the second whitespace in the header.
In this case you would specify the word index in the header that belongs to the annotated function.

`HyProFunc.sh -f fasta.faa -p 3`

## File descriptions

`/bin/AA_Sequence_Extract.py`  
    -Python script that uses Biopython to parse a .gbff or .gbk file and randomly extract a user-defined number of sequences based on a set seed.  
    -Example Usage: `AA_Sequence_Extract.py input_file.gbff 10`

`/bin/Comparison.py`  
    -Python script that merges two .csv files by the first column of each file, keeping all entries in the second file (right merge).  
    -Example Usage: `Comparison.py file_one.csv file_two.csv file/path/to/output_dir`

`/bin/ESMFold_API.py`  
    -Python script that utilizes the ESMFold API to predict protein structure based on a given amino acid sequence.  
    -Example Usage: `ESMFold_API.py input.faa output/dir/ path/to/ESM.pem`

`/bin/filter_files.py`  
    -Python script that updates the FILE_LIST in the Hypothetical_Protein_Function.sh script.

`/bin/filter_sort_fasta.py`  
    -Python script that uses Biopython to parse a fasta file, and filter out sequences shorter than the minimum length. Remaining sequences are sorted by length.  
    -Example Usage: `filter_sort_fasta.py input_fasta.faa output_fasta.faa 500`

`/bin/Foldseek_API.py`  
    -Python script that utilizes the Foldseek API to query the predicted protein structure against three alphafold databases.  
    -Example Usage: `Foldseek_API.py input.pdb output/dir/`

`/bin/Generate_substrings.py`  
    -Python script that parses the tabular Foldseek output and creates a sorted list of most common substrings at each substring length.  
    -Example Usage: `Generate_substrings.py Concatenated_foldseek_output.tsv`

`/bin/Header_functions.py`  
    -Python script that extracts the header ID and annotated function from a fasta header. Annotated function position can be indicated with a word number or RegEx.  
    -Example Usage: `Header_functions.py input.faa output/dir/` or `Header_functions.py input.faa output/dir/ 3` or `Header_functions.py input.faa output/dir/ r">.*(.*).*\s"`

`/bin/HSP.py`  
    -Python script that extracts the header IDs and their corresponding sequences from a fasta file and writes the data to a CSV file.  
    -Example Usage: `HSP.py input.faa path/to/output/dir/`

`/bin/Protein_function_inference.py`  
    -Python script to process the substrings.csv file and determine an inferred function.  
     While only the *Select*.csv file path is passed to the script, it assumes the corresponding *substrings*.csv file exists in the same location.  
    -Example Usage: `Protein_function_inference.py Select.csv`

`/bin/Remove_Fasta_Duplicates.py`  
    -Python script to remove duplicate fasta entries based on exact fasta sequence.  
    -Example Usage: `Remove_Fasta_Duplicates.py input.faa output.faa`

`/data/Example_data.fa`  
    -Three example fasta sequences extracted from the Sneathia vaginalis Sn35 annotated genome. This file can be used to confirm successful installation.

`/ESM.pem`  
    -Public SSL certificate chain for *secure ESMFold API access. This file needs to remain in the same directory as the bash script `Hypothetical_Protein_Function.sh`.  
     Workaround for "https://github.com/facebookresearch/esm/discussions/627".  
    *Hostname verification is disabled and certificate validation is bypassed, but SSL encryption is maintained.

`/Hypothetical_Protein_Function.sh`  
    -The main bash script that utilizes the above python scripts to infer a protein function based on a given amino acid sequence.
