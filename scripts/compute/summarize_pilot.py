"""Summarize exported real pilot artifacts without inventing completion."""
import argparse,datetime,hashlib,json,pathlib,re,subprocess,sys

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=pathlib.Path,default=pathlib.Path('results/compute/pilot'));ap.add_argument('--read-pairs',type=int,default=None);ap.add_argument('--status',choices=['completed','failed'],required=True);a=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parents[2];output=root/'results/compute';path=output/'pilot_summary.json';summary=json.loads(path.read_text())
    a.artifacts=a.artifacts.resolve()
    logs=a.artifacts/'logs';summary['status']=a.status;summary['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for key in ('wall_time_seconds','n_chimeric_junction_records','matched_pairs','matched_junctions','n_split_junction_records','n_encompassing_mate_records','n_unique_chimeric_fragments'):
        summary[key]=None
    validation_path=logs/'fastq_validation.json'
    if a.status=='completed' and not validation_path.exists():raise ValueError('completed run requires actual FASTQ validation')
    if validation_path.exists():
        validation=json.loads(validation_path.read_text())
        if validation['run_accession']!=summary['run_accession']:raise ValueError('run accession mismatch')
        if a.read_pairs is not None and a.read_pairs!=validation['paired_records']:raise ValueError('requested denominator differs from validated FASTQs')
        a.read_pairs=validation['paired_records']
        summary['read_pairs']=a.read_pairs
        summary['read_lengths']=validation['read_lengths']
        summary['sampling']=f'first {a.read_pairs} SRA spots; paired read lengths {validation["read_lengths"]}; deterministic bounded pilot'
        checksum_log=logs/'input_sha256.txt'
        if a.status=='completed' and not checksum_log.exists():raise ValueError('input checksum log missing')
        if checksum_log.exists():
            hashes={pathlib.Path(line.split(maxsplit=1)[1].strip()).name:line.split()[0] for line in checksum_log.read_text().splitlines()}
            for item in validation['files']:
                if hashes.get(item['name'])!=item['sha256']:raise ValueError('validation and alignment input checksums differ')
    elif a.status=='failed':
        summary['read_pairs']=None
        summary['read_lengths']=None
        summary['sampling']='FASTQ denominator unavailable in this failed run'
    if a.status=='failed':
        import shutil
        archive=output/'previous_selected_run'
        for name in ['evidence.tsv','parabricks_evidence.tsv','parabricks_junction_matches.tsv','parabricks_junction_matches_raw.tsv','match_manifest.json']:
            prior=output/name
            if prior.exists():
                archive.mkdir(exist_ok=True);shutil.copy2(prior,archive/name);prior.unlink()
    complete=logs/'completed_utc.txt'
    if a.status=='completed' and not complete.exists():raise ValueError('completion marker missing; cannot claim completed')
    if a.status=='completed':
        bam=a.artifacts/'output/SRR37513722.bam'
        if not bam.exists() or bam.stat().st_size==0:raise ValueError('nonempty BAM output required')
        qc=logs/'bam_quickcheck.exitcode'
        if not qc.exists() or qc.read_text().strip()!='0':raise ValueError('completed run requires successful samtools quickcheck')
    summary['pipeline_wall_time_seconds']=None
    if complete.exists() and (logs/'start_utc.txt').exists():
        start=datetime.datetime.fromisoformat((logs/'start_utc.txt').read_text().strip().replace('Z','+00:00'))
        end=datetime.datetime.fromisoformat(complete.read_text().strip().replace('Z','+00:00'))
        summary['pipeline_wall_time_seconds']=(end-start).total_seconds()
    summary['gpu_observed_peak_utilization_percent']=None
    summary['gpu_observed_peak_memory_mib']=None
    gpu_csv=logs/'gpu_utilization.csv'
    if gpu_csv.exists():
        import csv
        samples=list(csv.DictReader(gpu_csv.open()))
        for field,key in [('utilization_gpu_percent','gpu_observed_peak_utilization_percent'),('memory_used_mib','gpu_observed_peak_memory_mib')]:
            values=[]
            for sample in samples:
                try:values.append(float(sample[field]))
                except (ValueError,TypeError,KeyError):pass
            if values:summary[key]=max(values)
        summary['gpu_utilization_samples']=len(samples)
    log=(logs/'parabricks.log').read_text() if (logs/'parabricks.log').exists() else ''
    match=re.search(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([\d:.]+)',log)
    if match:
        parts=[float(p) for p in match.group(1).split(':')];summary['wall_time_seconds']=sum(x*60**i for i,x in enumerate(parts[::-1]))
    junctions=list((a.artifacts/'output').rglob('*Chimeric*out*junction*'))
    if a.status=='completed' and len(junctions)!=1:raise ValueError(f'Expected exactly one real junction file; found{junctions}')
    if junctions:
        records=[s.split('\t') for s in junctions[0].read_text().splitlines() if s.strip() and not s.startswith('#')]
        summary['n_chimeric_junction_records']=len(records)
        summary['n_split_junction_records']=sum(int(r[6])>=0 for r in records)
        summary['n_encompassing_mate_records']=sum(int(r[6])<0 for r in records)
        summary['n_unique_chimeric_fragments']=len({r[9] for r in records})
    if a.status=='completed':
        subprocess.run([sys.executable,str(root/'scripts/compute/match_junctions.py'),'--junctions',str(junctions[0]),'--probes',str(root/'results/dataset_reconstruction/probe_junctions.tsv'),'--output',str(output),'--read-pairs',str(a.read_pairs)],check=True)
        m=json.loads((output/'match_manifest.json').read_text());summary['matched_pairs']=m['matched_pairs']
        import pandas as pd
        matches=pd.read_csv(output/'parabricks_junction_matches.tsv',sep='\t')
        summary['matched_junctions']=len(matches[['pair_id','chrom1','terminal1','strand1','chrom2','terminal2','strand2']].drop_duplicates())
        (output/'evidence.tsv').write_bytes((output/'parabricks_evidence.tsv').read_bytes())
    summary['reference_provenance']='results/compute/pilot/logs/input_sha256.txt'
    summary['index_provenance']='results/compute/pilot/logs/genomeParameters.txt'
    summary['initial_failed_attempt_provenance']='results/compute/pilot/logs/parabricks_initial_parameter_failure.log'
    summary['artifacts']=[str(p.relative_to(root)) for p in [*logs.glob('*'),*junctions,output/'spending_manifest.json',output/'parabricks_evidence.tsv',output/'parabricks_junction_matches.tsv'] if p.exists()]
    summary['limitations']=[s for s in summary['limitations'] if not s.startswith(('Alignment not yet','No probe-panel junction matched','Actual pipeline failed'))]
    if a.status=='failed':summary['limitations'].insert(0,'Actual pipeline failed; logs document failure. No successful GPU-generated evidence claimed.')
    elif summary['matched_pairs']==0:summary['limitations'].insert(0,'No probe-panel junction matched in the tiny subsample; this is not evidence that the candidates are absent.')
    summary['artifact_sha256']={str(p.relative_to(root)):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in [*logs.glob('*'),*junctions] if p.is_file()}
    path.write_text(json.dumps(summary,indent=2));print(json.dumps({k:summary[k] for k in ['status','read_pairs','wall_time_seconds','n_chimeric_junction_records','matched_pairs','matched_junctions']},indent=2))
if __name__=='__main__':main()
