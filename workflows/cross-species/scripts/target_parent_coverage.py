"""Descriptive parent-gene coverage only; never a chRNA rescue call."""
import pathlib,json,sys,csv,re,collections
import pysam
R=pathlib.Path(__file__).resolve().parents[1];sp,run=sys.argv[1:3];targets=set(json.loads((R/'review/coverage_targets.json').read_text())[sp]);exons=collections.defaultdict(list)
for l in (R/'reference'/sp/'adapted/typhon.gtf').open():
 if l.startswith('#'):continue
 f=l.rstrip().split('\t')
 if f[2]!='exon':continue
 g=re.search(r'gene_id "([^"]+)"',f[8]).group(1)
 if g in targets:exons[g].append((f[0],int(f[3])-1,int(f[4])))
bychrom=collections.defaultdict(list)
for g,es in exons.items():
 merged=[]
 for chrom,s,e in sorted(set(es)):
  if merged and chrom==merged[-1][0] and s<=merged[-1][2]:merged[-1]=(chrom,merged[-1][1],max(e,merged[-1][2]))
  else:merged.append((chrom,s,e))
 for chrom in {e[0] for e in merged}:
  sub=[(s,e) for c,s,e in merged if c==chrom];bychrom[chrom].append((g,min(s for s,e in sub),max(e for s,e in sub),sub))
coverage=collections.defaultdict(dict)
with pysam.AlignmentFile(R/'per_species'/sp/run/'longgf_results'/(run+'.bam'),'rb') as bam:
 for a in bam:
  if a.is_unmapped or a.is_secondary or a.mapping_quality<20:continue
  for g,s,e,es in bychrom.get(a.reference_name,[]):
   if a.reference_start>=e or a.reference_end<=s:continue
   overlap=sum(max(0,min(ee,y)-max(ss,x)) for x,y in a.get_blocks() for ss,ee in es)
   if overlap>=100:coverage[g][a.query_name]=max(overlap,coverage[g].get(a.query_name,0))
rows=[{'species':sp,'run':run,'gene_id':g,'gene_in_annotation':g in exons,'reads_with_MAPQ20_and_100nt_exonic_overlap':len(coverage[g]),'interpretation':'parent coverage only; not chimeric support or junction coverage'} for g in sorted(targets)]
with (R/'per_species'/sp/run/'target_parent_coverage.tsv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
print(sp,len(rows),'target genes assessed')
