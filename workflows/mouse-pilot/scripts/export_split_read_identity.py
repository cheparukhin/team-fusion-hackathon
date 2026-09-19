"""Export the validated SRA-alias/original-NAME correspondence for audit reads."""
import csv
import hashlib
import json
from pathlib import Path

from chrna.read_intake import HEADER


base=Path(__file__).resolve().parents[1]/'runs/focused-pilot-20260919'
validation=json.loads((base/'discovery-validation.json').read_text())
rows=[]
with (base/'discovery/split_reads.fastq').open() as source:
    for number in range(validation['split_reads']):
        header=source.readline().rstrip('\n')
        sequence,separator,quality=[source.readline().rstrip('\n') for _ in range(3)]
        match=HEADER.fullmatch(header)
        if match is None or len(sequence)!=len(quality):raise ValueError('Unexpected validated FASTQ format')
        accession,spot,read,original=match.groups()
        rows.append({'read_alias':header.split()[0][1:],'original_read_name':original,'run_accession':accession,
                     'spot_id':int(spot),'read_number':int(read),'split_fastq_record_number':number+1,
                     'source_fastq_header':header})
    if source.readline():raise ValueError('Unexpected extra split FASTQ records')
assert len({r['read_alias'] for r in rows})==len(rows)
assert len({r['original_read_name'] for r in rows})==len(rows)
target=base/'read_identity.tsv'
with target.open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]) if rows else ['read_alias','original_read_name'],delimiter='\t')
    writer.writeheader();writer.writerows(rows)
receipt={'rows':len(rows),'identity_tsv_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
         'source_fastq_sha256':validation['verified_sha256']['split_reads.fastq'],
         'original_name_validation':'Full input FASTQ headers were independently checked against archive NAME in runs/pilot-20260919/intake_validation.json.',
         'read_alias_semantics':'SRA run.spot/read alias used by SAM/LongGF; original archive NAME is retained without replacement.'}
(base/'read_identity.provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
