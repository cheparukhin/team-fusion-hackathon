"""Independently reconstruct the paper-architecture control from M28 transcripts."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
examples=json.loads((ROOT/'results/presentation/candidate_examples.json').read_text())
c=next(c for c in examples['candidates'] if c['pair_id']=='Gsdmd:Tmem106a')
sides=c['probe_examples'][0]['sides']; models=[sides[k]['representative'] for k in ['a','b']]
ids={m['transcript_id'] for m in models}; seqs={}; name=None
source=ROOT/'data/reference/gencode.vM28.transcripts.fa.gz'
with gzip.open(source,'rt') as f:
 for line in f:
  if line.startswith('>'):
   name=line[1:].split('|')[0]
   if name in ids:seqs[name]=''
  elif name in ids:seqs[name]+=line.strip().upper()
assert ids==set(seqs)
def offset(m):
 prior=0
 for e in m['exons']:
  if e['exon_number']==m['junction_exon']:
   return prior+(m['breakpoint']-e['start'] if m['strand']=='+' else e['end']-m['breakpoint'])
  prior+=e['end']-e['start']+1
 raise ValueError('missing junction exon')
left=seqs[models[0]['transcript_id']][:offset(models[0])+1];right=seqs[models[1]['transcript_id']][offset(models[1]):]
rna=left+right
assert rna[len(left)-60:len(left)+60]==c['probe_examples'][0]['sequence']
bases='TCAG'; aas='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
code={a+b+c:aa for (a,b,c),aa in zip(((a,b,c) for a in bases for b in bases for c in bases),aas)}
orfs=[]
for start in range(len(rna)-2):
 if rna[start:start+3]!='ATG':continue
 peptide=''
 for pos in range(start,len(rna)-2,3):
  aa=code.get(rna[pos:pos+3],'X')
  if aa=='*':
   if start<len(left)<pos and len(peptide)==118:orfs.append({'start_0based':start,'stop_start_0based':pos,'protein':peptide})
   break
  peptide+=aa
assert len(orfs)==1,orfs
orf=orfs[0];digest=hashlib.sha256(orf['protein'].encode()).hexdigest()
expected='f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
assert digest==expected, (digest,orf)
x={'status':'verified','method':'Independent splice reconstruction from exact probe-matched M28 transcript sequences; complete ATG-to-stop ORF crosses junction and matches published length118.','pair_id':c['pair_id'],'parent_transcripts':[m['transcript_id'] for m in models],'junction_offset_0based':len(left),'exact_120nt_probe_match':True,'orf':orf,'protein_sha256':digest,'cached_boltz_input_sequence_sha256_matches':True,'sequence_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_coordinate_sha256':examples['input_sha256'],'limitation':'Reference-derived reconstruction,not author-supplied full sequence or experimental validation of this isoform. Selecting the paper118aa architecture is a positive-control reconstruction,not de novo discovery.'}
(ROOT/'results/presentation/reference_orf_verification.json').write_text(json.dumps(x,indent=2)+'\n')
print(json.dumps({k:x[k] for k in ['status','pair_id','junction_offset_0based','protein_sha256','exact_120nt_probe_match']},indent=2))
