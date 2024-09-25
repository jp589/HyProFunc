#!/usr/bin/env python

from requests import get, post
from time import sleep
import sys

# opens .pdb file and queries the structure against the alphafold databases.
with open(sys.argv[1], 'rb') as file:
    input_pdb = {'q': file}
    params = {
            'mode': '3diaa',
            'taxfilter': '2',
            'database[]' : ['afdb50', 'afdb-swissprot','afdb-proteome']
             }
    # submit a new job
    ticket = post('https://search.foldseek.com/api/ticket', files = input_pdb, data=params).json()
    #debug statement
    #print(ticket)
    if ticket['status'] == 'RATELIMIT':
        print("Foldseek API rate limit reached. :(")
        #we create a ratelimit file.
        with open(sys.argv[2] + 'RateLimitReached', 'a') as f:
            pass
        sys.exit()

# poll until the job was successful or failed
repeat = True
while repeat:
    status = get('https://search.foldseek.com/api/ticket/' + ticket['id']).json()
    if status['status'] == "ERROR":
        # handle error
        print("Foldseek ticket status was error. :(")
        sys.exit(1)

    # wait a short time between poll requests
    sleep(1)
    repeat = status['status'] != "COMPLETE"

# get all hits for the first query (0)
result = get('https://search.foldseek.com/api/result/' + ticket['id'] + '/0').json()

# download blast compatible result archive
download = get('https://search.foldseek.com/api/result/download/' + ticket['id'], stream=True)
with open(sys.argv[2] + 'result.tar.gz', 'wb') as fd:
    #print("writing result.tar.gz")
    for chunk in download.iter_content(chunk_size=128):
        fd.write(chunk)
