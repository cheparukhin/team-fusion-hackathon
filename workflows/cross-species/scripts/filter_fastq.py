import argparse,gzip,json,pathlib,math,collections
p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('target',type=pathlib.Path);a=p.parse_args();a.target.parent.mkdir(parents=True,exist_ok=True)
errors=[10**(-q/10) for q in range(94)];counts=collections.Counter();names=set();hist=collections.Counter()
with gzip.open(a.source,'rt') as src,gzip.open(str(a.target)+'.part','wt',compresslevel=1) as dst:
 while True:
  h=src.readline()
  if not h:break
  s=src.readline();plus=src.readline();q=src.readline();seq=s.rstrip();qual=q.rstrip()
  if not h.startswith('@') or not plus.startswith('+') or len(seq)!=len(qual) or not qual:raise ValueError('Invalid FASTQ')
  rid=h.split()[0][1:]
  if rid in names:raise ValueError('Duplicate read ID '+rid)
  names.add(rid);counts['input_reads']+=1;counts['input_bases']+=len(seq)
  meanq=-10*math.log10(sum(errors[ord(c)-33] for c in qual)/len(qual));hist[int(meanq)]+=1
  if meanq>=7:
   dst.write(h+s+plus+q);counts['retained_reads']+=1;counts['retained_bases']+=len(seq)
pathlib.Path(str(a.target)+'.part').rename(a.target)
a.target.with_suffix('.qc.json').write_text(json.dumps({'counts':counts,'quality_histogram':hist,'minimum_mean_error_probability_phred':7,'minimum_length':0,'read_ids':'unchanged; duplicates cause failure','source':str(a.source)},indent=2))
