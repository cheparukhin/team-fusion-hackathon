"""Reviewable Genion PASS evidence, with statistical failures retained as exploratory."""
import pathlib,csv,json,sys,collections,re,gzip
import pysam
R=pathlib.Path(__file__).resolve().parents[1];species,run=sys.argv[1:3];out=R/'per_species'/species/run;ref=next(x for x in json.loads((R/'manifest/references.json').read_text()) if x['species']==species)
raw=list(csv.reader((out/'genion_results'/(run+'_genion.tsv')).open(),delimiter='\t'));calls=[]
for x in raw:
 if x[9].startswith('PASS'):
  genes=x[7].split('::')
  if len(genes)==2:calls.append({'genes':genes,'read_id':x[27],'genion_flag':x[9],'statistical_flag':x[25]})
wanted={g for c in calls for g in c['genes']};exons=collections.defaultdict(list);symbols={};strands={}
gtf=R/'reference'/species/'adapted/typhon.gtf'
for l in gtf.open():
 if l.startswith('#'):continue
 f=l.rstrip().split('\t')
 if f[2]!='exon':continue
 m=re.search(r'gene_id "([^"]+)"',f[8]);g=m.group(1)
 if g in wanted:exons[g].append((f[0],int(f[3])-1,int(f[4])));strands[g]=f[6]
# Merge exon intervals across transcript isoforms so shared exons cannot inflate coverage.
for g,es in exons.items():
 merged=[]
 for chrom,s,e in sorted(set(es)):
  if merged and merged[-1][0]==chrom and s<=merged[-1][2]:merged[-1]=(chrom,merged[-1][1],max(e,merged[-1][2]))
  else:merged.append((chrom,s,e))
 exons[g]=merged
ids={c['read_id'] for c in calls};byread=collections.defaultdict(list)
with pysam.AlignmentFile(out/'longgf_results'/(run+'.bam'),'rb') as src,pysam.AlignmentFile(out/'genion_evidence.bam','wb',template=src) as dst:
 for a in src:
  if a.query_name in ids:byread[a.query_name].append(a);dst.write(a)
def arm(g,alignments):
 chunks=[]
 for a in alignments:
  if a.is_unmapped or a.is_secondary:continue
  q=0;r=a.reference_start;L=a.infer_read_length()
  for op,n in a.cigartuples:
   if op in [0,7,8]:
    for chrom,s,e in exons[g]:
     if chrom!=a.reference_name:continue
     lo=max(s,r);hi=min(e,r+n)
     if hi<=lo:continue
     qs=q+lo-r;qe=q+hi-r
     if a.is_reverse:qs,qe=L-qe,L-qs
     chunks.append((qs,qe,chrom,lo,hi,'-' if a.is_reverse else '+',a.mapping_quality))
    q+=n;r+=n
   elif op in [1,4,5]:q+=n
   elif op in [2,3]:r+=n
 if not chunks:return None
 chunks.sort();first=chunks[0];last=max(chunks,key=lambda c:c[1]);intervals=[]
 for c in chunks:
  if intervals and c[0]<=intervals[-1][1]:intervals[-1][1]=max(intervals[-1][1],c[1])
  else:intervals.append([c[0],c[1]])
 return {'gene':g,'chrom':first[2],'strand':first[5],'qstart':first[0],'qend':last[1],'boundary_start':first[3] if first[5]=='+' else first[4],'boundary_end':last[4] if last[5]=='+' else last[3],'aligned_nt':sum(e-s for s,e in intervals),'mapq':min(c[6] for c in chunks),'native_gene_strand':strands.get(g,'')}
original={}
mp=R/'raw'/run/'read_id_map.tsv.gz'
if mp.exists():
 with gzip.open(mp,'rt') as f:original={r['archive_read_id']:r['original_read_id'] for r in csv.DictReader(f,delimiter='\t') if r['archive_read_id'] in ids}
rows=[]
for c in calls:
 a,b=[arm(g,byread[c['read_id']]) for g in c['genes']]
 if not a or not b:continue
 a,b=sorted([a,b],key=lambda x:(x['qstart']+x['qend'])/2)
 row={'species':species,'assembly':ref['assembly'],'run':run,'read_id':c['read_id'],'original_read_id':original.get(c['read_id'],''),'caller':'Genion','genion_flag':c['genion_flag'],'statistical_flag':c['statistical_flag'],'gene5':a['gene'],'gene3':b['gene'],'chrom5':a['chrom'],'chrom3':b['chrom'],'strand5':a['strand'],'strand3':b['strand'],'boundary5_0based':a['boundary_end'],'boundary3_0based':b['boundary_start'],'query_gap_nt':b['qstart']-a['qend'],'mapq5':a['mapq'],'mapq3':b['mapq'],'aligned_nt5':a['aligned_nt'],'aligned_nt3':b['aligned_nt'],'qstart5':a['qstart'],'qend5':a['qend'],'qstart3':b['qstart'],'qend3':b['qend'],'alignment_qc_pass':a['mapq']>=20 and b['mapq']>=20 and a['aligned_nt']>=100 and b['aligned_nt']>=100 and b['qstart']-a['qend']>=-25,'caller_statistical_pass':c['statistical_flag']=='pPASS','status':'observed exon-aligned boundaries; not exon-repaired; not conserved'}
 rows.append(row)
with (out/'genion_read_evidence.tsv').open('w') as f:
 fields=list(rows[0]) if rows else ['species','run','read_id','gene5','gene3','status'];w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)
(out/'genion_evidence_summary.json').write_text(json.dumps({'debug_rows':len(raw),'morphology_PASS_rows':len(calls),'normalized_rows':len(rows),'unique_PASS_reads':len(ids),'alignment_qc_PASS_reads':len({r['read_id'] for r in rows if r['alignment_qc_pass']}),'alignment_and_statistical_PASS_reads':len({r['read_id'] for r in rows if r['alignment_qc_pass'] and r['caller_statistical_pass']}),'statistical_failures':'retained separately, not accepted strict evidence','unresolved_order_or_arms':len(calls)-len(rows)},indent=2))
print(species,len(rows),'Genion records')
