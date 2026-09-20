from pathlib import Path
import subprocess,json,hashlib,datetime
R=Path(__file__).resolve().parents[1]
paths=[]
for sp,run in [('homo_sapiens','SRR31438987'),('bos_taurus','SRR31429688')]:
 d=Path('per_species')/sp/run
 for name in ['evidence_reads.fastq.gz','longgf_evidence.bam','genion_evidence.bam','longgf_read_evidence.tsv','genion_read_evidence.tsv','target_parent_coverage.tsv','genion_results/'+run+'_genion.tsv','longgf_results/'+run+'.log','review_reconstruction/exon_repair/Merged_seqs_exon_repair_renamed.fa','review_reconstruction/exon_repair/native_exon_segments.tsv','review_reconstruction/exon_repair/independent_validation.json','review_reconstruction/exon_repair/selected_exons.numeric_exon_number.bed']:
  paths.append(str(d/name))
script='import pathlib,json,hashlib\nr=pathlib.Path("/home/ubuntu/cross-species")\npaths='+repr(paths)+'\nprint(json.dumps({p:hashlib.sha256((r/p).read_bytes()).hexdigest() for p in paths}))\n'
p=subprocess.run(['ssh','-T','chrna-cross-species-20260920','python3','-'],input=script,text=True,capture_output=True,check=True)
remote=json.loads(p.stdout);results=[]
for path,digest in remote.items():
 local=hashlib.sha256((R/path).read_bytes()).hexdigest();assert local==digest,path
 results.append({'path':path,'sha256':digest,'local_matches_remote':True})
(R/'qc/remote_export_verification.json').write_text(json.dumps({'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','files':results},indent=2)+'\n')
print('PASS:',len(results),'critical evidence files match remote SHA256')
