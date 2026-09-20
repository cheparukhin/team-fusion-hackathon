"""Verify campaign arithmetic, sequence identity, saved scores and artifact provenance."""
import hashlib,json
from pathlib import Path
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[2];b=ROOT/'results/structure_campaign'
checks={}
def check(name,value):
 checks[name]=bool(value)
 if not value:raise AssertionError(name)
for area in ['cohort','domains','diversity']:
 m=json.loads((b/area/'manifest.json').read_text())
 for rel,digest in m['output_sha256'].items():check(f'{area}:{rel}:sha256',hashlib.sha256((b/area/rel).read_bytes()).hexdigest()==digest)
r=pd.read_csv(b/'cohort/reference_candidates.tsv',sep='\t');check('383_reference_pairs',len(r)==383 and r.pair_id.nunique()==383);check('109_primary_rna_pairs',r.primary_reference.sum()==109)
p=pd.read_csv(b/'cohort/peptides.tsv',sep='\t');conditional=p[p.conditional_census_eligible];check('188_conditional_unique_peptides',len(conditional)==188 and conditional.sequence_sha256.nunique()==188);check('0_strict_primary_peptides',not p.strict_primary_eligible.any())
for folder,count in [('analysis',188),('analysis/alternative_start',746),('analysis/controls',529)]:
 t=pd.read_csv(b/folder/'disorder_summary.tsv',sep='\t');profiles=json.loads((b/folder/'profiles.json').read_text());check(f'{folder}:count',len(t)==count)
 for row in t.itertuples():
  scores=np.asarray(profiles[row.peptide_id]['metapredict_v3']);seq=profiles[row.peptide_id]['sequence']
  check(f'{folder}:{row.peptide_id}:sequence',len(scores)==len(seq)==row.length and hashlib.sha256(seq.encode()).hexdigest()==row.sequence_sha256)
  check(f'{folder}:{row.peptide_id}:f_idr',abs(float((scores>=.5).mean())-row.f_idr)<1e-12)
x=pd.read_csv(b/'analysis/disorder_summary.tsv',sep='\t');check('42_V3_predominantly_disordered',x.f_idr.gt(.5).sum()==42);check('18_V1_predominantly_disordered',x.v1_f_idr.gt(.5).sum()==18)
selection=pd.read_csv(b/'selection/selection.tsv',sep='\t');check('frozen51_selected_sequences',len(selection)==51 and selection.sequence_sha256.nunique()==51);check('no_primary_promotion',selection.role.eq('primary').sum()==0)
sm=json.loads((b/'selection/manifest.json').read_text())
for path,digest in sm['inputs'].items():check(f'selection:{path}:sha256',hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest)
jobs=json.loads((b/'compute/jobs.json').read_text());verified=[j for j in jobs if j['status']in ['verified','cached_verified']]
for job in verified:
 for name,digest in job.get('artifact_sha256',{}).items():check(f"model:{job['job_id']}:{name}:sha256",hashlib.sha256(Path(job['artifacts'][name]).read_bytes()).hexdigest()==digest)
check('unique_job_ids',len({j['job_id']for j in jobs})==len(jobs))
diversity=json.loads((b/'analysis/diversity_summary.json').read_text())
check('diversity_final_jobs_snapshot',diversity['input_jobs_sha256']==hashlib.sha256((b/'compute/jobs.json').read_bytes()).hexdigest())
repeat_manifest=b/'selection/seed_repeats/manifest.json'
if repeat_manifest.exists():
 repeat=json.loads(repeat_manifest.read_text())
 check('repeat_selection_source_snapshot',hashlib.sha256((ROOT/repeat['source_metrics_snapshot']).read_bytes()).hexdigest()==repeat['source_metrics_sha256'])
 for name,digest in repeat['output_sha256'].items():check(f'repeat_selection:{name}:sha256',hashlib.sha256((repeat_manifest.parent/name).read_bytes()).hexdigest()==digest)
summary=json.loads((b/'summary_provenance.json').read_text())
for path,digest in summary['inputs'].items():check(f'summary:{path}:sha256',hashlib.sha256((b/path).read_bytes()).hexdigest()==digest)
check('results_summary_output_sha256',hashlib.sha256((b/'RESULTS.md').read_bytes()).hexdigest()==summary['output_sha256'])
evidence=pd.read_csv(b/'analysis/candidate_evidence_table.tsv',sep='\t')
check('evidence188_unique_sequence_hypotheses',len(evidence)==188 and evidence.sequence_sha256.nunique()==188 and set(evidence.sequence_sha256)==set(conditional.sequence_sha256))
for protocol,prefix in [('boltz2_2.2.1_single_sequence','single_sequence'),('boltz2_2.2.1_precomputed','msa_backed')]:
 modeled={j['sequence_sha256']for j in verified if j['protocol_id']==protocol and j['seed']==20260919}
 check(f'evidence:{protocol}:available_firstseed_only',evidence[prefix+'_model_available'].eq(evidence.sequence_sha256.isin(modeled)).all())
result={'status':'passed','checks_passed':len(checks),'strict_primary_peptides':0,'conditional_peptides':188,'alternative_start_peptides':746,'control_peptides':529,'actual_verified_model_jobs':len(verified),'checks':checks,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(b/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='checks'},indent=2))
