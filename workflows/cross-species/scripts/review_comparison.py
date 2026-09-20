import pathlib,csv,collections,json
from compare_pairs import orthology_lookup,matches
R=pathlib.Path(__file__).resolve().parents[1]
with (R/'reference/orthology/five_species_homologies.tsv').open() as f:orth=orthology_lookup(csv.DictReader(f,delimiter='\t'))
allrows=[];symbols={}
for sp,run in [('homo_sapiens','SRR31438987'),('bos_taurus','SRR31429688')]:
 symbols[sp]={r['gene_id']:r['original_gene_name'] for r in csv.DictReader((R/'reference'/sp/'adapted/gene_names.tsv').open(),delimiter='\t')}
 for caller in ['longgf','genion']:
  p=R/'per_species'/sp/run/(caller+'_read_evidence.tsv')
  if p.exists():
   for r in csv.DictReader(p.open(),delimiter='\t'):
    r['symbol5']=symbols[sp].get(r['gene5'],'');r['symbol3']=symbols[sp].get(r['gene3'],'');allrows.append(r)
def eligible(r,tier):
 q=r.get('alignment_qc_pass')=='True';stat=r['caller']!='Genion' or r.get('caller_statistical_pass')=='True'
 if tier=='primary_candidate':return q and stat
 if tier=='exploratory_including_statistical_failures':return q
 return True
outputs=[];counts={}
for tier in ['primary_candidate','exploratory_including_statistical_failures','all_reported_including_low_MAPQ']:
 groups={}
 for r in allrows:
  if not eligible(r,tier):continue
  key=(r['species'],r['gene5'],r['gene3']);g=groups.setdefault(key,dict(species=key[0],gene5=key[1],gene3=key[2],reads=set(),callers=set(),records=[]))
  g['reads'].add(r['original_read_id'] or r['run']+':'+r['read_id']);g['callers'].add(r['caller']);g['records'].append(r)
 humans=[g for g in groups.values() if g['species']=='homo_sapiens'];cows=[g for g in groups.values() if g['species']=='bos_taurus'];shared=[]
 for a in humans:
  for b in cows:
   if matches(a,b,orth):
    row={'tier':tier,'classification':'ordered_parent_pair_shared_only','junction_conservation':'not_established','human_gene5':a['gene5'],'human_gene3':a['gene3'],'cow_gene5':b['gene5'],'cow_gene3':b['gene3'],'human_symbols':symbols['homo_sapiens'].get(a['gene5'],'')+'--'+symbols['homo_sapiens'].get(a['gene3'],''),'cow_symbols':symbols['bos_taurus'].get(b['gene5'],'')+'--'+symbols['bos_taurus'].get(b['gene3'],''),'human_unique_reads':len(a['reads']),'cow_unique_reads':len(b['reads']),'human_callers':';'.join(sorted(a['callers'])),'cow_callers':';'.join(sorted(b['callers'])),'biological_samples_per_species':1,'human_read_ids':';'.join(sorted({r['read_id'] for r in a['records']})),'cow_read_ids':';'.join(sorted({r['read_id'] for r in b['records']}))};shared.append(row);outputs.append(row)
 counts[tier]={'human_ordered_pairs':len(humans),'cow_ordered_pairs':len(cows),'shared_ordered_pairs':len(shared),'human_pairs_with_both_one_to_one_cow_orthologs':sum(all((a['species'],a[g],'bos_taurus') in orth for g in ['gene5','gene3']) for a in humans)}
 fields=list(outputs[0]) if outputs else ['tier','classification','junction_conservation','human_gene5','human_gene3','cow_gene5','cow_gene3']
with (R/'comparison/reviewed_pair_matches.tsv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(outputs)
(R/'comparison/comparison_summary.json').write_text(json.dumps({'scope':'one human run versus one cow run; preliminary','tiers':counts,'conserved_chRNAs_established':0,'reason':'Ordered-pair recurrence alone cannot establish homologous junctions or biological replication'},indent=2))
# Lossless evidence union; blanks indicate caller-specific fields not available.
fields=list(dict.fromkeys(k for r in allrows for k in r))
with (R/'comparison/all_read_evidence.tsv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(allrows)
print(json.dumps(counts,indent=2));print(json.dumps(outputs,indent=2))
