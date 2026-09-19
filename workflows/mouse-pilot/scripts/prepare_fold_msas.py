"""Prepare a frozen batch's MSAs serially, recording bounded service failures."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def save(path,value):
    temporary=path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


def main(inputs):
    root=Path(__file__).resolve().parents[1]
    manifest_path=inputs/'manifest.json';manifest=json.loads(manifest_path.read_text())
    cache=root/'runs/focused-pilot-20260919/msa-cache';cache.mkdir(exist_ok=True)
    cutoff=min(time.time()+1800,datetime(2026,9,19,20,tzinfo=timezone.utc).timestamp())
    history=[]
    for job in manifest['jobs']:
        destination=inputs/job['msa'];sidecar=destination.with_suffix('.json')
        started=time.monotonic()
        record={'job_id':job['job_id'],'sequence_sha256':job['sequence_sha256'],'started_utc':datetime.now(timezone.utc).isoformat()}
        try:
            if not (destination.exists() and sidecar.exists()):
                remaining=cutoff-time.time()
                if remaining<30:
                    raise TimeoutError('MSA batch deadline reached')
                directory=cache/job['job_id'];directory.mkdir(exist_ok=True)
                with (directory/'preparation.log').open('a') as log:
                    status=subprocess.run([sys.executable,str(root/'scripts/prepare_boltz_msa.py'),
                        '--fasta',str(inputs/job['fasta']),'--output',str(directory)],
                        cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=min(900,remaining),check=False).returncode
                if status:raise RuntimeError('MSA client exited '+str(status))
                shutil.copyfile(directory/'alignment.a3m',destination)
                shutil.copyfile(directory/'msa.json',sidecar)
            receipt=json.loads(sidecar.read_text())
            if receipt['sequence_sha256']!=job['sequence_sha256'] or hashlib.sha256(destination.read_bytes()).hexdigest()!=receipt['a3m_sha256']:
                raise ValueError('MSA cache integrity mismatch')
            record.update(status='verified',rows=receipt['rows'],msa_wall_seconds=receipt['wall_seconds'],a3m_sha256=receipt['a3m_sha256'])
        except Exception as error:
            record.update(status='unavailable',error=str(error),error_type=type(error).__name__)
        record.update(wall_seconds=time.monotonic()-started,finished_utc=datetime.now(timezone.utc).isoformat())
        history.append(record);save(inputs/'msa-preparation.json',history)
    available={r['job_id'] for r in history if r['status']=='verified'}
    ordered=sorted((j for j in manifest['jobs'] if j['job_id'] in available),key=lambda j:(j['amino_acids'],j['job_id']))
    (inputs/'manifest.pre-msa.json').write_text(manifest_path.read_text())
    manifest['timing_pilot_job_ids']=[ordered[i]['job_id'] for i in sorted({0,len(ordered)//2,len(ordered)-1})] if ordered else []
    manifest['msa_plan_updated_utc']=datetime.now(timezone.utc).isoformat()
    manifest['msa_unavailable_job_ids']=[r['job_id'] for r in history if r['status']=='unavailable']
    manifest['timing_policy']='Shortest, median and longest sequences among verified available MSAs; retain unavailable selected sequences as explicit compute deferrals.'
    for job in manifest['jobs']:
        job['stage']='msa_unavailable' if job['job_id'] not in available else ('timing_pilot' if job['job_id'] in manifest['timing_pilot_job_ids'] else 'production_after_timing_review')
    save(manifest_path,manifest)
    print(json.dumps({'verified':len(available),'unavailable':len(history)-len(available),'timing_pilot':manifest['timing_pilot_job_ids']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    main(parser.parse_args().inputs.resolve())
