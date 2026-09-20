"""Orthologous ordered-pair recurrence only; never labels junction conservation."""
import csv,pathlib,collections,itertools,json
R=pathlib.Path(__file__).resolve().parents[1]
def orthology_lookup(rows):
 lookup={}
 for r in rows:
  if r['homology_type']!='ortholog_one2one':continue
  a=(r['species'],r['gene_stable_id']);b=(r['homology_species'],r['homology_gene_stable_id'])
  for x,y in [(a,b),(b,a)]:
   key=(x[0],x[1],y[0]);prior=lookup.get(key)
   if prior is not None and prior!=y[1]:raise ValueError('Nonunique one-to-one mapping: '+str(key))
   lookup[key]=y[1]
 return lookup
def matches(a,b,lookup):
 return a['species']!=b['species'] and lookup.get((a['species'],a['gene5'],b['species']))==b['gene5'] and lookup.get((a['species'],a['gene3'],b['species']))==b['gene3']
def main():
 with (R/'reference/orthology/five_species_homologies.tsv').open() as f:lookup=orthology_lookup(csv.DictReader(f,delimiter='\t'))
 samples={r['run_accession']:r for r in csv.DictReader((R/'manifest/samples.tsv').open(),delimiter='\t')};groups={}
 for p in (R/'per_species').glob('*/*/longgf_read_evidence.tsv'):
  for r in csv.DictReader(p.open(),delimiter='\t'):
   if r.get('alignment_qc_pass')!='True':continue
   k=(r['species'],r['gene5'],r['gene3']);g=groups.setdefault(k,{'species':k[0],'gene5':k[1],'gene3':k[2],'reads':set(),'samples':set(),'runs':set()});g['reads'].add(r['original_read_id'] or r['run']+':'+r['read_id']);g['runs'].add(r['run']);s=samples[r['run']]['biological_sample_id']
   if s!='UNRESOLVED':g['samples'].add(s)
 pairs=[]
 for a,b in itertools.combinations(groups.values(),2):
  if matches(a,b,lookup):
   row={'classification':'ordered_parent_pair_shared_only','junction_conserved':'not_evaluated','caller_scope':'LongGF preliminary'}
   for label,g in [('a',a),('b',b)]:
    for field in ['species','gene5','gene3']:row[field+'_'+label]=g[field]
    row['reads_'+label]=len(g['reads']);row['biological_samples_'+label]=len(g['samples']);row['runs_'+label]=';'.join(sorted(g['runs']))
   pairs.append(row)
 out=R/'comparison';out.mkdir(exist_ok=True)
 with (out/'preliminary_ordered_pair_matches.tsv').open('w') as f:
  fields=list(pairs[0]) if pairs else ['classification','junction_conserved','caller_scope','species_a','gene5_a','gene3_a','species_b','gene5_b','gene3_b']
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(pairs)
 (out/'preliminary_pair_status.json').write_text(json.dumps({'species_with_QC_passing_LongGF_evidence':sorted({g['species'] for g in groups.values()}),'ordered_pairs':len(groups),'cross_species_ordered_pair_matches':len(pairs),'status':'partial caller/sample coverage; not a conserved-chRNA list','missing_species':'not biological negatives'},indent=2))
if __name__=='__main__':main()
