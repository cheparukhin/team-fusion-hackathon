"""Preserve ordered read-level evidence; these are unvalidated LongGF candidates."""
import pathlib,re,csv,json,sys,gzip,collections
import pysam
R=pathlib.Path(__file__).resolve().parents[1];species,run=sys.argv[1:3];out=R/'per_species'/species/run;lg=out/'longgf_results';ref=next(x for x in json.loads((R/'manifest/references.json').read_text()) if x['species']==species)
# LongGF log coordinates are 0-based inclusive, confirmed by synthetic fixture.
pat=re.compile(r'^\s*(\d+)\(([+-])([^:]+):(\d+)-(\d+)/(.*):(\d+)-(\d+)\)\d+\s+(\d+)\(([+-])([^:]+):(\d+)-(\d+)/(\d+)-(\d+)\)\d+')
rows=[];pair=None
for line in (lg/(run+'.log')).open():
 if line.startswith('GF\t'):pair=line.split()[1].split(':');continue
 m=pat.match(line)
 if not m:continue
 z=m.groups();rid=z[5]
 arms=[{'gene':pair[0],'chrom':z[2],'strand':z[1],'start':int(z[3]),'end':int(z[4])+1,'qstart':int(z[6]),'qend':int(z[7])+1},{'gene':pair[1],'chrom':z[10],'strand':z[9],'start':int(z[11]),'end':int(z[12])+1,'qstart':int(z[13]),'qend':int(z[14])+1}]
 arms.sort(key=lambda a:a['qstart']);a,b=arms
 row={'species':species,'assembly':ref['assembly'],'run':run,'read_id':rid,'caller':'LongGF','gene5':a['gene'],'gene3':b['gene'],'chrom5':a['chrom'],'chrom3':b['chrom'],'strand5':a['strand'],'strand3':b['strand'],'boundary5_0based':a['end'] if a['strand']=='+' else a['start'],'boundary3_0based':b['start'] if b['strand']=='+' else b['end'],'query_gap_nt':b['qstart']-a['qend'],'status':'unvalidated_caller_evidence'}
 for suffix,arm in [('5',a),('3',b)]:
  for k in ['start','end','qstart','qend']:row[k+suffix]=arm[k]
 rows.append(row)
ids={r['read_id'] for r in rows};alns=collections.defaultdict(list)
with pysam.AlignmentFile(lg/(run+'.bam'),'rb') as src,pysam.AlignmentFile(out/'longgf_evidence.bam','wb',template=src) as dst:
 for a in src:
  if a.query_name in ids:alns[a.query_name].append(a);dst.write(a)
mapfile=R/'raw'/run/'read_id_map.tsv.gz';original={}
if mapfile.exists():
 with gzip.open(mapfile,'rt') as f:
  original={x['archive_read_id']:x['original_read_id'] for x in csv.DictReader(f,delimiter='\t') if x['archive_read_id'] in ids}
for row in rows:
 row['original_read_id']=original.get(row['read_id'],'')
 for side in ['5','3']:
  matches=[a for a in alns[row['read_id']] if not a.is_unmapped and a.reference_name==row['chrom'+side] and a.reference_start==row['start'+side] and a.reference_end==row['end'+side] and ('-' if a.is_reverse else '+')==row['strand'+side]]
  row['mapq'+side]=max((a.mapping_quality for a in matches),default=-1)
  row['aligned_nt'+side]=max((sum(n for op,n in a.cigartuples if op in [0,7,8]) for a in matches),default=-1)
 row['alignment_qc_pass']=all(row['mapq'+s]>=20 and row['aligned_nt'+s]>=100 for s in ['5','3'])
with (out/'longgf_read_evidence.tsv').open('w') as f:
 if rows:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
 else:f.write('species\tassembly\trun\tread_id\tstatus\n')
(out/'longgf_evidence_summary.json').write_text(json.dumps({'read_evidence_rows':len(rows),'unique_read_ids':len(ids),'ordered_pairs':len({(r['gene5'],r['gene3']) for r in rows}),'alignment_qc_passing_reads':len({r['read_id'] for r in rows if r['alignment_qc_pass']}),'coordinate_convention':'genomic between-base boundaries 0-based; interval starts inclusive ends exclusive','conservation':'not evaluated','biological_validation':'pending other callers, parent checking, exon reconstruction, replication'},indent=2))
print('Normalized',len(rows),'evidence records')
