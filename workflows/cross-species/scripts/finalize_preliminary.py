"""Freeze and validate the deadline-limited preliminary scientific evidence."""
from pathlib import Path
import csv, json, gzip, hashlib, struct, datetime
R=Path(__file__).resolve().parents[1]
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def rows(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def bam_ids(p):
 with gzip.open(p,'rb') as f:
  assert f.read(4)==b'BAM\1'
  f.read(struct.unpack('<i',f.read(4))[0])
  for _ in range(struct.unpack('<i',f.read(4))[0]):
   f.read(struct.unpack('<i',f.read(4))[0]);f.read(4)
  result=set();records=0
  while True:
   n=f.read(4)
   if not n:break
   block=f.read(struct.unpack('<i',n)[0]);nl=block[8]
   result.add(block[32:32+nl-1].decode());records+=1
  return result,records
checks=[]
for species,run,expected,models in [('homo_sapiens','SRR31438987',43,37),('bos_taurus','SRR31429688',1085,200)]:
 p=R/'per_species'/species/run;ids=set()
 with gzip.open(p/'evidence_reads.fastq.gz','rt') as f:
  while True:
   h=f.readline()
   if not h:break
   s=f.readline().strip();plus=f.readline();q=f.readline().strip()
   assert h.startswith('@') and plus.startswith('+') and len(s)==len(q)
   rid=h[1:].split()[0];assert rid not in ids;ids.add(rid)
 assert len(ids)==expected
 union=set();bams={}
 for caller in ['longgf','genion']:
  rr=rows(p/(caller+'_read_evidence.tsv'));wanted={x['read_id'] for x in rr};union.update(wanted)
  actual,n=bam_ids(p/(caller+'_evidence.bam'))
  assert actual==wanted,(species,caller,actual^wanted)
  bams[caller]={'unique_read_ids':len(actual),'alignment_records':n,'exact_match_to_evidence_table':True}
 assert ids==union
 iv=json.loads((p/'review_reconstruction/exon_repair/independent_validation.json').read_text())
 assert iv['exact_sequence_matches']==models and not iv['extra_fasta_ids'] and not iv['missing_fasta_ids']
 checks.append({'species':species,'run':run,'FASTQ_records':len(ids),'FASTQ_equals_normalized_candidate_union':True,'BAM_validation':bams,'independently_validated_reference_models':models})
cat=rows(R/'comparison/candidate_pair_catalog.tsv')
for sp,n,comparable in [('homo_sapiens',25,19),('bos_taurus',153,85)]:
 primary=[r for r in cat if r['species']==sp and int(r['primary_unique_reads'])>0]
 assert len(primary)==n
 assert sum(r['both_parents_one_to_one_comparable']=='True' for r in primary)==comparable
assert len(rows(R/'review/reviewed_top_cases.tsv'))==10
assert not rows(R/'comparison/conserved_chRNAs.tsv')
assert not rows(R/'comparison/reviewed_pair_matches.tsv')
(R/'qc/final_evidence_validation.json').write_text(json.dumps({'validated_utc':now,'status':'PASS','scope':'Export integrity, candidate identity, summary consistency; not biological validation','checks':checks},indent=2)+'\n')
(R/'qc/analysis_freeze.json').write_text(json.dumps({'frozen_utc':now,'scope':'Preliminary human SRR31438987 and cow SRR31429688','scientific_analysis':'frozen','shared_primary_ordered_ortholog_pairs':0,'conserved_chRNAs_established':0,'no_further_scope_expansion':True},indent=2)+'\n')
report=R/'PRELIMINARY_REPORT.md'
s=report.read_text().replace('Genion also requires its statistical `pPASS` flag;','Genion additionally limits the overlap between parent query intervals to 25 nt and requires its statistical `pPASS` flag;')
report.write_text(s)
qc=R/'qc/caller_compatibility.md'
s=qc.read_text().replace('- Actual biological caller outputs and reconstruction still require validation. Successful installation is not successful integration.','- LongGF and Genion completed for the two pilot libraries. Human Genion completed at 11:29:01 UTC, evidenced by its execution log and valid output, although the terminated continuation driver did not write a stage receipt.\n- Human JAFFAL failed with `std::out_of_range: map::at` during transcript lookup; cow JAFFAL was interrupted at the caller cutoff. Both are unavailable, never biological negatives.\n- TYPHON exon reconstruction required a selected-transcript BED quoting conversion (`exon_number "N"` to `exon_number N`). Coordinates, IDs, numeric values and sequences were unchanged. All 37 human and 200 cow recovered sequences passed independent native-genome concatenation checks, but many repaired boundaries differ from observed read alignments.\n- Full three-caller TYPHON integration and biological validation were not achieved.')
qc.write_text(s)
stages=[('input_identity_and_checksums','complete','two runs only'),('LongGF','complete','both species; output_flag=16'),('Genion','complete','both species; statistical flags preserved'),('JAFFAL_human','failed','transcript lookup std::out_of_range map::at'),('JAFFAL_cow','interrupted','not completed by 11:36:10 UTC cutoff'),('LongGF_reference_reconstruction','complete_with_caveats','237 independently sequence-checked models; boundary uncertainty retained'),('ordered_ortholog_pair_comparison','complete','zero shared pairs'),('top_case_review','complete','ten single-species pairs'),('homologous_cross_species_junctions','not_established','no shared pair candidate; genome mapping not performed'),('biological_replication','not_performed','one biological sample per species'),('other_species_and_remaining_samples','not_performed','excluded from revised deadline scope'),('three_caller_integrated_TYPHON','not_achieved','JAFFAL unavailable'),('experimental_validation','not_performed','computational preliminary findings only')]
with (R/'qc/completed_vs_pending.tsv').open('w') as f:
 w=csv.writer(f,delimiter='\t');w.writerow(['component','status','detail']);w.writerows(stages)
(R/'per_species/bos_taurus/SRR31429688/jaffal_deadline_status.json').write_text(json.dumps({'status':'interrupted/unavailable','basis':'Deadline scheduler terminated unfinished caller group at 11:36:10 UTC; no completed JAFFAL result','recorded_utc':now,'biological_negative':False},indent=2)+'\n')
(R/'per_species/homo_sapiens/SRR31438987/genion_completion_review.json').write_text(json.dumps({'status':'completed, output reviewed','basis':'genion_execution.log records successful completion at 11:29:01 UTC; 439 debug rows and six two-parent PASS records parsed','missing_driver_receipt':'Continuation parent was terminated to prevent sequential caller blocking','recorded_utc':now},indent=2)+'\n')
print(json.dumps(checks,indent=2))
