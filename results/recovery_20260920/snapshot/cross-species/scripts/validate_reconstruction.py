import pathlib,sys,csv,collections,json
import pysam
R=pathlib.Path(__file__).resolve().parents[1];sp,run=sys.argv[1:3];out=R/'per_species'/sp/run;work=out/'review_reconstruction/exon_repair';ref=next(x for x in json.loads((R/'manifest/references.json').read_text()) if x['species']==sp);genome=R/'reference'/sp/ref['genome_url'].split('/')[-1][:-3]
fa=pysam.FastaFile(str(genome));arms={};segments=[];comp=str.maketrans('ACGTNacgtn','TGCANtgcan')
for side in ['A','B']:
 d=collections.defaultdict(list)
 with (work/('bed_file_'+side+'.bed')).open() as f:
  for chrom,start,end,rid,qual,strand in csv.reader(f,delimiter='\t'):
   seq=fa.fetch(chrom,int(start),int(end))
   if strand=='-':seq=seq.translate(comp)[::-1]
   d[rid].append(seq);segments.append({'read_id':rid,'side':side,'chrom':chrom,'start_0based':start,'end_0based_exclusive':end,'strand':strand})
 arms[side]={r:''.join(ss) for r,ss in d.items()}
expected={r:arms['A'][r]+arms['B'][r] for r in arms['A'] if r in arms['B']};actual={};rid=None
for l in (work/'Merged_seqs_exon_repair_renamed.fa').open():
 if l.startswith('>'):rid=l[1:].strip().split()[0];actual[rid]=''
 else:actual[rid]+=l.strip()
checks=[]
for rid,seq in expected.items():checks.append({'read_id':rid,'expected_length':len(seq),'reconstructed_length':len(actual.get(rid,'')),'sequence_matches_independent_native_exon_fetch':actual.get(rid,'').upper()==seq.upper(),'reconstructed_junction_offset':len(arms['A'][rid])})
with (work/'independent_sequence_checks.tsv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(checks[0]),delimiter='\t');w.writeheader();w.writerows(checks)
with (work/'native_exon_segments.tsv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(segments[0]),delimiter='\t');w.writeheader();w.writerows(segments)
summary={'expected_read_models':len(expected),'actual_FASTA_records':len(actual),'exact_sequence_matches':sum(r['sequence_matches_independent_native_exon_fetch'] for r in checks),'extra_fasta_ids':sorted(set(actual)-set(expected)),'missing_fasta_ids':sorted(set(expected)-set(actual)),'validation_scope':'Reconstruction sequence equals strand-aware native genomic exon concatenation. Does not validate biological origin, observed full-length sequence, or cross-species conservation.'}
(work/'independent_validation.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));assert summary['exact_sequence_matches']==len(expected) and not summary['extra_fasta_ids']
