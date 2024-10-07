#!/usr/bin/env bash

USAGE=$(cat <<-END
Usage:
    $(basename "$0") [-h] [-c] [-e] [-r] [-g genome.gbff] [-f fasta.faa] [-p 3]

-h  Displays help page.
-c  Optional flag to compare protein function annotation in header sequence to this script's output.
-e  Optional flag to extract amino acid sequences denoted as hypothetical in the fasta header.
-g  Optional .gbff or .gbk file from which amino acid sequences will randomly be extracted and compared to this script's output.
-r  Optional flag to remove duplicate fasta entries.
-f  Fasta file containing amino acid sequences.
-p  Optional word number (character string separated by whitespace) or regex pattern to match annotated function in fasta header.
    Default behavior is to extract all characters after the second whitespace.
    This is only needed when comparing functional annotation in the header sequence to this script's output.
    Example generic regex pattern: 'r">.*(.*).*\s"'

Header sequence IDs are determined by default as the characters immediately following the '>' until the first whitespace.
These IDs will be used for intermediate file naming so try to avoid special characters.
However, '|', '(', and ')' will be converted to '_' before Header sequence ID extraction if present.

This script determines protein function based on the amino acid sequences provided in a fasta format.

If the '-c' option is used with '-g', only the fasta file derived from the .gbff file will be used for protein function determination.

Keep in mind that the Biopython module is required to parse the .gbff or .gbk file if included.

Each sequence is trimmed to the first 400 amino acids and then submitted to the ESMFold API:
    "https://api.esmatlas.com/foldSequence/v1/pdb/"
The subsequently generated .pdb file is sumbitted to the Foldseek API:
    "https://search.foldseek.com/api/ticket"
as a query against three Alphafold databases: AFDB50, AFDB-SWISSPROT, AFDB-PROTEOME.
This results in a table of structurally similar proteins.
The descriptions are parsed to determine the most common substring.
This substring is reported along with the header, percentage of descriptions containing the substring,
the average SeqID, and the sequence submitted to ESMFold.

Please keep in mind that this script utilizes APIs that are considered shared resources.
As such, the ESMFold API is limited to 50 requests at a time,
and the Foldseek API request loop will break after the rate limit has been reached.

Please also note that the ESMFold API has known SSL certificate issues:
    "https://github.com/facebookresearch/esm/discussions/627"

This script makes use of a custom SSL connection that disables hostname verification and bypasses
certificate validation, but SSL encryption is maintained for data transfer.

END
)

# Initialize variables
GBFF=""
ORIGINAL_FASTA=""
COMPARE=false
EXTRACT=false
REMOVE_DUPS=false
PATTERN=""

while getopts "h?cerg:f:p:" opt; do
    case "$opt" in
    h|\?)
        echo "$USAGE"
        exit 0
        ;;
    c)  COMPARE=true
        ;;
    e)  EXTRACT=true
        ;;
    r)  REMOVE_DUPS=true
        ;;
    g)  GBFF="${OPTARG}"
        ;;
    f)  ORIGINAL_FASTA="${OPTARG}"
        ;;
    p) PATTERN="${OPTARG}"
        ;;
    esac
done

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Get the current date and time in the format hh-mm-ss
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
log_file="HPFlog_${TIMESTAMP}.log"

# Redirect both stdout (1) and stderr (2) to tee, appending to the log file
exec > >(tee -a "$log_file") 2>&1

echo "HyProFunc started at $TIMESTAMP"
echo "Your current working directory is: $(pwd)"
echo "The bash script directory was: $SCRIPT_DIR"

# silent logging
echo "Option -c was '$COMPARE'" >> "$log_file"
echo "Option -e was '$EXTRACT'" >> "$log_file"
echo "Option -r was '$REMOVE_DUPS'" >> "$log_file"
echo "Option -g was '$GBFF'" >> "$log_file"
echo "Option -f was '$ORIGINAL_FASTA'" >> "$log_file"
echo "Option -p was '$PATTERN'" >> "$log_file"

D="${SCRIPT_DIR}"

# checks to make sure inputs and options are good to go
# 1. Check if gbff and fasta are both included
if [[ -n "${GBFF:-}" && -n "${ORIGINAL_FASTA:-}" ]]; then
    echo "'-g' and '-f' are mutually exclusive. Only one can be used as input."
    exit 1
fi

# if gbff file input, perform AA sequence extraction
if [[ -n "${GBFF}" ]]; then
    read -p "How many sequences should randomly be extracted from ${GBFF}? " NUM_SEQS_TO_EXTRACT
    echo "${NUM_SEQS_TO_EXTRACT} random amino acid sequences will be extracted from ${GBFF}."
    #Once extracted, now we need to reroute original fasta
    "${D}"/bin/AA_Sequence_Extract.py ${GBFF} ${NUM_SEQS_TO_EXTRACT} | tee FastaFilePath.txt
    ORIGINAL_FASTA=$(tail -n 1 FastaFilePath.txt | awk '{print $NF}')
    echo $ORIGINAL_FASTA
fi


FASTA_FN="${ORIGINAL_FASTA%.*}"

# optional extraction of hypothetical proteins
if [[ "$EXTRACT" == "true" ]]; then
    echo "Extracting hypothetical proteins from ${ORIGINAL_FASTA}"
    awk '/^>/ {header = $0} /hypothetical/ && /^>/ {print header; next} /^>/ {header=""; next} header {print}' \
    ${ORIGINAL_FASTA} > ${FASTA_FN}_hypothetical.faa
    FASTA=${FASTA_FN}_hypothetical.faa
    echo "Extracted hypothetical proteins saved in ${FASTA}"
else
    FASTA=${ORIGINAL_FASTA}
fi

# optional removal of duplicate fasta entries (AA sequence must match exactly)
if [[ "$REMOVE_DUPS" == "true" ]]; then
    FASTA_PRE="${FASTA%.*}"
    echo "Removing duplicate fasta entries from ${FASTA}"
    "${D}"/bin/Remove_Fasta_Duplicates.py ${FASTA} ${FASTA_PRE}_nodups.faa
    FASTB=${FASTA_PRE}_nodups
    echo "Created file: ${FASTA_PRE}_nodups.faa"
else
    FASTB="${FASTA%.*}"
fi

if [ ! -d "./$FASTB" ]; then
  mkdir ./$FASTB
  echo "Directory $FASTB created."
else
  echo "Directory $FASTB already exists."
fi

#optional processing of original fasta file to extract annotated functions from headers
if [[ "$COMPARE" == "true" ]]; then
    echo "Extracting protein functions from fasta headers in ${ORIGINAL_FASTA} for future comparison."
    "${D}"/bin/Header_functions.py ${ORIGINAL_FASTA} ./${FASTB}/ ${PATTERN}
fi

"${D}"/bin/ESMFold_API.py ${FASTA} ./${FASTB}/ "${D}"/ESM.pem

for PDB in ./${FASTB}/*.pdb
    do
    BASE="${PDB%.*}"
    BNAME=$(basename "$BASE")
    if [[ -f "./${FASTB}/${BNAME}_no_prob_one" ]]; then
        echo "Skipping Foldseek for $PDB because Foldseek has already been run and no hits were found with prob = 1."
        continue
    elif [[ -f "./${FASTB}/${BNAME}_empty" ]]; then
        echo "Skipping Foldseek for $PDB because Foldseek has already been run and no hits were found."
        continue
    elif [[ -f "./${FASTB}/${BNAME}_no_info" ]]; then
        echo "Skipping Foldseek for $PDB because Foldseek has already been run and no informative hits were found."
        continue
    fi
    if [[ -f "./${FASTB}/substrings_${BNAME}.csv" && -f "./${FASTB}/Select_${BNAME}.csv" ]]
        then echo "Skipping Foldseek for $PDB because substrings_${BNAME}.csv and Select_${BNAME}.csv found"
    else
        if [[ -f "./${FASTB}/result.tar.gz" ]]; then rm ./${FASTB}/result.tar.gz; fi
        echo "Processing $PDB with Foldseek"
        "${D}"/bin/Foldseek_API.py ${PDB} ./${FASTB}/
        if [[ -f "./${FASTB}/RateLimitReached" ]] ; then
            echo "Exiting Foldseek loop!"
            break
        elif [[ -f "./${FASTB}/result.tar.gz" ]]; then
            #script uses three databases so results are output in three .m8 files after unzipping
            tar -xzf ./${FASTB}/result.tar.gz -C ./${FASTB}
            cat ./${FASTB}/*.m8 > ${BASE}.tsv; rm ./${FASTB}/*.m8; rm ./${FASTB}/result.tar.gz
            echo "Generating substrings for $BASE"
            "${D}"/bin/Generate_substrings.py ${BASE}.tsv; rm ${BASE}.tsv
        else
            echo "Exit status = $? : Foldseek API request not completed for ${PDB}. Skipping substring generation."
        fi
    fi
done

if [[ -f "./${FASTB}/RateLimitReached" ]]; then rm ./${FASTB}/RateLimitReached; fi

if [[ -f "./${FASTB}/Protein_Functions.csv" ]]; then
     # determine which files have already been processed and remove them from the loop.
     "${D}"/bin/filter_files.py ./${FASTB}/Protein_Functions.csv ./${FASTB}/ 'Select_*.csv' print_values
     FILE_LIST=$("${D}"/bin/filter_files.py ./${FASTB}/Protein_Functions.csv ./${FASTB}/ 'Select_*.csv')
else
    FILE_LIST=$(ls ./${FASTB}/Select_*.csv)
fi

#for SELECT in ./${FASTB}/Select_*.csv; do
for SELECT in $FILE_LIST; do
    SBNAME=$(basename "${SELECT%.*}")
    echo "Determining protein function for sequence $SBNAME"
    "${D}"/bin/Protein_function_inference.py ${SELECT}
done

NUM_FUNCTIONS_DETERMINED=$(($(wc -l ./${FASTB}/Protein_Functions.csv | tr ' ' '\n' | head -1) - 1))
NUM_UNSUCCESSFUL=$(ls ./${FASTB}/*{no_prob_one,empty,no_info} 2>/dev/null | wc -l)

NUM_ATTEMPTED=$(($NUM_FUNCTIONS_DETERMINED + $NUM_UNSUCCESSFUL))
TOTAL=$(head -1 ./${FASTB}/num_entries)
#TOTAL=$(($(wc -l ./${FASTB}/Header_Sequence.csv | tr ' ' '\n' | head -1) - 1))

echo "Report:"
echo "${NUM_FUNCTIONS_DETERMINED} protein functions have been determined."
echo "${NUM_UNSUCCESSFUL} protein functions were unable to be determined."
echo "${NUM_ATTEMPTED} protein function determinations have been attempted out of ${TOTAL} total protein functions to be determined."
if [[ "$NUM_ATTEMPTED" -eq "$TOTAL" && "$NUM_ATTEMPTED" -gt 0 ]]; then
    echo "Run complete. All amino acid sequences have been checked."
elif [[ "$NUM_ATTEMPTED" -lt "$TOTAL" ]]; then
    echo "Script will need to be rerun to check all amino acid sequences."
fi

if [[ "$COMPARE" == "true" && -f "./${FASTB}/Original_Header_Function.csv" ]]; then
    echo "Comparing annotated functions to determined functions."
    "${D}"/bin/Comparison.py ./${FASTB}/Original_Header_Function.csv ./${FASTB}/Protein_Functions.csv ./${FASTB}/
fi
