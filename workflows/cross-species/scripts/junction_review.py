import pathlib,csv,collections,json
R=pathlib.Path(__file__).resolve().parents[1];allrows=list(csv.DictReader((R/'comparison/all_read_evidence.tsv').open(),delimiter='\t'));raw={(r['species'],r['read_id']):r for r in allrows if r['caller']=='LongGF'};out=[]
for sp,run in [('homo_sapiens','SRR31438987'),('bos_taurus','SRR31429688')]:
 p=R/'per_species'/sp/run/'review_reconstruction/exon_repair/phase4_summary_exon_data.csv';groups=collections.defaultdict(list)
 for r in csv.DictReader(p.open()):groups[r['Read_ID']].append(r)
 for rid,rows in groups.items():
  arms=[]
  for side in ['A','B']:
   matches=[r for r in rows if r['Actual_order']==side and float(r['exon_number'])==float(r['breakpoint_exon'])]
   signatures={(r['Exon_chromosome'],r['Exon_chromosome_start'],r['Exon_chromosome_end'],r['Exon_strand'],r['Transcript_ID']) for r in matches}
   if len(signatures)!=1:break
   r=matches[0];start=int(float(r['Exon_chromosome_start']));end=int(float(r['Exon_chromosome_end']));strand=r['Exon_strand'];boundary=(end if strand=='+' else start) if side=='A' else (start if strand=='+' else end)
   arms.append({'gene':r.get('Gene_x',r.get('Gene','')),'transcript':r['Transcript_ID'],'chrom':r['Exon_chromosome'],'strand':strand,'boundary':boundary,'exon':int(float(r['exon_number']))})
  if len(arms)!=2:continue
  a,b=arms;orig=raw[(sp,rid)];same=(a['gene'],b['gene'])==(orig['gene5'],orig['gene3']);d5=abs(a['boundary']-int(orig['boundary5_0based'])) if same else '';d3=abs(b['boundary']-int(orig['boundary3_0based'])) if same else ''
  out.append({'species':sp,'run':run,'read_id':rid,'gene5':a['gene'],'gene3':b['gene'],'transcript5_adapter_name':a['transcript'],'transcript3_adapter_name':b['transcript'],'exon5':a['exon'],'exon3':b['exon'],'reconstructed_boundary5_0based':a['boundary'],'reconstructed_boundary3_0based':b['boundary'],'gene_order_agrees_with_read_alignment':same,'shift5_nt':d5,'shift3_nt':d3,'within_10nt_both_boundaries':same and d5<=10 and d3<=10,'alignment_qc_pass':orig['alignment_qc_pass'],'scope':'reference-assisted single-species junction; no cross-species homology established'})
with (R/'review/junction_review.tsv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(out[0]),delimiter='\t');w.writeheader();w.writerows(out)
summary={sp:{'reviewed_models':sum(r['species']==sp for r in out),'same_gene_order':sum(r['species']==sp and r['gene_order_agrees_with_read_alignment'] for r in out),'both_boundaries_within_10nt_of_observed_alignment':sum(r['species']==sp and r['within_10nt_both_boundaries'] for r in out),'QC_and_boundary_agreement':sum(r['species']==sp and r['within_10nt_both_boundaries'] and r['alignment_qc_pass']=='True' for r in out)} for sp in ['homo_sapiens','bos_taurus']}
(R/'review/junction_review_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
for r in out:
 if r['gene5']=='ENSG00000117151':print(r)
