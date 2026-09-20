import pathlib,csv,gzip,json,sys
R=pathlib.Path(__file__).resolve().parents[1];sp,run=sys.argv[1:3];out=R/'per_species'/sp/run;ids=set()
for name in ['longgf_read_evidence.tsv','genion_read_evidence.tsv']:
 p=out/name
 if p.exists():ids.update(r['read_id'] for r in csv.DictReader(p.open(),delimiter='\t'))
found=set();dest=out/'evidence_reads.fastq.gz'
with gzip.open(R/'raw'/run/(run+'.fastq.gz'),'rt') as src,gzip.open(str(dest)+'.part','wt') as dst:
 while True:
  h=src.readline()
  if not h:break
  s=src.readline();p=src.readline();q=src.readline();rid=h[1:].split()[0]
  if rid in ids:dst.write(h+s+p+q);found.add(rid)
assert found==ids, str(ids-found)
pathlib.Path(str(dest)+'.part').rename(dest)
(out/'evidence_read_export.json').write_text(json.dumps({'requested_unique_reads':len(ids),'exported_unique_reads':len(found),'source':'Original deposited FASTQ; original full header, sequence and quality unchanged','includes':'Completed LongGF candidates and normalized Genion PASS candidates, including explicitly flagged lower-confidence evidence'},indent=2))
print(sp,len(found),'reads preserved')
