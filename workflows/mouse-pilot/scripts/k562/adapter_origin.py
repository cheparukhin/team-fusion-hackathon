"""Sequence-only artifact screen; flags are not biological truth labels."""
from pathlib import Path
import collections,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from chrna.pilot_orfs import revcomp
BASE=ROOT/'runs/k562-extension-20260920';OLD=ROOT/'runs/k562-pilot/20260919-overnight/outputs'
CORES={'RTA_A':'GGCTTCTTCTTGCTCTTAGGTAGTAGGTTC','RTA_B_non_polyT':'GAGGCGAGCGGTCAATTTTCCTAAGAGCAAGAAGAAGCC'}
SOURCES=['https://nanoporetech.com/document/direct-rna-sequencing-sequence-specific-sqk-rna004','https://pmc.ncbi.nlm.nih.gov/articles/PMC11895459/','https://nanoporetech.com/document/direct-rna-sequencing-sqk-rna002']
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def approx_hits(pattern,text):
 """Full-pattern semiglobal Levenshtein search; target ends are free."""
 previous=[(0,j) for j in range(len(text)+1)]
 for i,base in enumerate(pattern,1):
  current=[(i,0)]
  for j,t in enumerate(text,1):
   choices=[(previous[j][0]+1,previous[j][1]),(current[j-1][0]+1,current[j-1][1]),(previous[j-1][0]+(base!=t),previous[j-1][1])]
   current.append(min(choices))
  previous=current
 hits=[{'start':start,'end':end,'edits':score,'pattern_length':len(pattern)} for end,(score,start) in enumerate(previous) if score<=len(pattern)//5 and end>start]
 chosen=[]
 for hit in sorted(hits,key=lambda x:(x['edits'],x['start'],x['end'])):
  if not any(hit['start']<h['end'] and hit['end']>h['start'] for h in chosen):chosen.append(hit)
 return sorted(chosen,key=lambda h:h['start'])
def screen(seq,bounds):
 hits=[]
 for name,core in CORES.items():
  for strand,p in [('+',core),('-',revcomp(core))]:
   for h in approx_hits(p,seq):
    internal=h['start']>=50 and len(seq)-h['end']>=50
    near=h['start']<=bounds[1]+75 and h['end']>=bounds[0]-75
    hits.append({**h,'adapter_core':name,'orientation':strand,'internal_50nt_flanks':internal,'within_75nt_of_join':near,'internal_near_join_flag':internal and near})
 tracts=[{'start':m.start(),'end':m.end(),'base':m.group()[0],'length':len(m.group())} for m in re.finditer(r'A{10,}|T{10,}',seq) if m.start()>=50 and len(seq)-m.end()>=50 and m.start()<=bounds[1]+75 and m.end()>=bounds[0]-75]
 return {'adapter_core_hits':hits,'internal_adapter_near_join':any(h['internal_near_join_flag'] for h in hits),'internal_polyAT_near_join':tracts,'adapter_interpretation':'sequence_similarity_flag' if any(h['internal_near_join_flag'] for h in hits) else 'no_full_core_match_at_prespecified_threshold','raw_signal_assessment':'NOT_PERFORMED','artifact_truth':'UNKNOWN'}
def main():
 rules={'cores':CORES,'sources':SOURCES,'method':'Full-core semiglobal Levenshtein, both orientations; <=floor(0.2*core length) edits','internal':'At least 50 nt from both read ends','near_join':'Adapter interval intersects join interval +/-75 nt','homopolymer':'A or T run >=10 nt, same internal and near-join bounds','limitations':['Not all RNA002 RMX/motor adapters are represented.','Partial-core fragments and raw-signal read concatenation are not resolved.','Basecalled RNA may not represent the DNA adapters faithfully.','No hit is not proof of an artifact-free molecule.','Homopolymers can be biological; flags do not alter frozen RNA ranking.']}
 save(BASE/'adapter-rules.json',rules)
 decisions=json.loads((BASE/'read_decisions.json').read_text());bylib=collections.defaultdict(list)
 for d in decisions:bylib[d['sample_alias']].append(d)
 records=[]
 for sample,ds in bylib.items():
  wanted={d['read_id'] for d in ds};sequences={}
  with (OLD/sample/'discovery/split_reads.fastq').open() as f:
   while h:=f.readline():
    seq=f.readline().strip();plus=f.readline();qual=f.readline().strip();rid=h[1:].split()[0]
    if rid in wanted:sequences[rid]=(seq,qual)
  assert sequences.keys()==wanted
  for d in ds:
   seq,qual=sequences[d['read_id']];bounds=sorted([d['left_alignment']['qend'],d['right_alignment']['qstart']])
   records.append({'junction_id':d['junction_id'],'read_id':d['read_id'],'library':d['library'],'rna_state':d['state'],'read_length':len(seq),'sequence_sha256':hashlib.sha256(seq.encode()).hexdigest(),'junction_query_interval':bounds,**screen(seq,bounds)})
 save(BASE/'adapter-read-assessment.json',records)
 summaries=[]
 for jid in json.loads((BASE/'scope-freeze.json').read_text())['junction_ids']:
  d=next(x for x in decisions if x['junction_id']==jid);rs=[r for r in records if r['junction_id']==jid];same=d['chromosome_5p']==d['chromosome_3p'];strand=d['strand_5p']==d['strand_3p'];delta=d['boundary_3p']-d['boundary_5p'];downstream=(delta>0 if d['strand_5p']=='+' else delta<0) if same and strand else None
  origin='interchromosomal; simple colinear reference read-through cannot explain it' if not same else 'opposite strands; simple colinear reference read-through cannot explain it' if not strand else 'same strand and downstream in reference; read-through is one unproven possibility' if downstream else 'reverse genomic order for the strand; simple colinear reference read-through cannot explain it'
  summaries.append({'junction_id':jid,'pair':d['gene_name_5p']+':'+d['gene_name_3p'],'assessed_reads':len(rs),'internal_adapter_flagged_reads':sum(r['internal_adapter_near_join'] for r in rs),'internal_polyAT_flagged_reads':sum(bool(r['internal_polyAT_near_join']) for r in rs),'origin_geometry':origin,'signed_reference_boundary_distance_nt':delta if same else None,'gene_biotypes':[d['biotype_5p'],d['biotype_3p']],'same_culture_DNA':'UNAVAILABLE','rna_origin':'UNRESOLVED','control_context':'BCR:ABL1 DNA-fusion detection control; sample-specific DNA not assessed' if d['gene_name_5p']=='BCR' and d['gene_name_3p']=='ABL1' else None,'mechanism_limit':'Reference geometry cannot distinguish rearrangement, RNA processing, or technical joining. Protein function unknown.'})
 save(BASE/'adapter-origin-summary.json',summaries);print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
