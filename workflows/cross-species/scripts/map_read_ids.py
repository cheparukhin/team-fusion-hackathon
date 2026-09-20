import gzip,pathlib,sys,csv,json,re
source=pathlib.Path(sys.argv[1]);target=source.parent/'read_id_map.tsv.gz';n=0;uuid=0
with gzip.open(source,'rt') as src,gzip.open(str(target)+'.part','wt') as dst:
 w=csv.writer(dst,delimiter='\t');w.writerow(['archive_read_id','original_read_id','original_header'])
 while True:
  h=src.readline()
  if not h:break
  for i in range(3):
   if not src.readline():raise ValueError('Truncated FASTQ')
  tokens=h[1:].strip().split();archive=tokens[0];original=tokens[1] if len(tokens)>1 else ''
  if re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}(?:/1)?',original):original=original.removesuffix('/1');uuid+=1
  w.writerow([archive,original,h[1:].rstrip()]);n+=1
pathlib.Path(str(target)+'.part').rename(target)
target.with_suffix('.json').write_text(json.dumps({'input_reads':n,'recognized_original_nanopore_uuids':uuid,'source':str(source),'original_header_preserved':True},indent=2))
print(n,'read identifiers mapped')
