"""Run a frozen, bounded monomer batch with measured timing and verified outputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import urllib.request


def save(path, record):
    temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('w') as stream:
        json.dump(record,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(8*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def weights(manifest, cache):
    cache.mkdir(exist_ok=True)
    verified=[]
    for row in manifest['files']:
        path=cache/row['rfilename']
        expected=row['lfs']['sha256']
        if not path.exists() or path.stat().st_size!=row['size'] or digest(path)!=expected:
            url=f'https://huggingface.co/boltz-community/boltz-2/resolve/{manifest["revision"]}/{row["rfilename"]}'
            partial=path.with_suffix(path.suffix+'.partial')
            with urllib.request.urlopen(url,timeout=120) as response, partial.open('wb') as target:
                while block:=response.read(8*1024*1024):
                    target.write(block)
            if partial.stat().st_size!=row['size'] or digest(partial)!=expected:
                raise ValueError('Model or molecule-cache download hash mismatch: '+path.name)
            partial.replace(path)
        verified.append({'filename':path.name,'sha256':expected,'bytes':path.stat().st_size})
    if not (cache/'mols').exists():
        with tarfile.open(cache/'mols.tar') as archive:
            for member in archive:
                target=cache/member.name
                if not target.resolve().is_relative_to(cache.resolve()):
                    raise ValueError('Molecule archive path escapes cache')
                if member.isdir():
                    target.mkdir(parents=True,exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with archive.extractfile(member) as source, target.open('wb') as out:
                        while block:=source.read(1024*1024):out.write(block)
                else:
                    raise ValueError('Unexpected non-regular molecule archive entry')
    return verified


def validate(job, directory):
    import gemmi
    import numpy as np
    predicted=directory/('boltz_results_'+job['job_id'])/'predictions'/job['job_id']
    cif=predicted/(job['job_id']+'_model_0.cif')
    structure=gemmi.read_structure(str(cif))
    if len(structure)!=1 or len(structure[0])!=1:
        raise ValueError('Expected one model and one protein chain')
    residues=list(structure[0][0])
    sequence=''.join(gemmi.find_tabulated_residue(r.name).one_letter_code.upper() for r in residues)
    if sequence!=job['sequence']:
        raise ValueError('Predicted structure sequence does not match frozen input')
    for residue in residues:
        atoms=[a for a in residue if a.name=='CA']
        if len(atoms)!=1 or not all(math.isfinite(v) for v in (atoms[0].pos.x,atoms[0].pos.y,atoms[0].pos.z)):
            raise ValueError('Missing, duplicated or non-finite alpha carbon')
    plddt=np.load(predicted/f'plddt_{job["job_id"]}_model_0.npz')['plddt'].squeeze()
    pae=np.load(predicted/f'pae_{job["job_id"]}_model_0.npz')['pae'].squeeze()
    length=len(sequence)
    if plddt.shape!=(length,) or not np.isfinite(plddt).all() or not ((plddt>=0)&(plddt<=1)).all():
        raise ValueError('Expected per-residue Boltz pLDDT on the 0–1 scale')
    if pae.shape!=(length,length) or not np.isfinite(pae).all() or (pae<0).any():
        raise ValueError('Invalid predicted aligned error matrix')
    confidence=json.loads((predicted/f'confidence_{job["job_id"]}_model_0.json').read_text())
    return {'status':'sequence_and_confidence_verified','sequence_sha256':hashlib.sha256(sequence.encode()).hexdigest(),
            'amino_acids':length,'mean_plddt_0_to_100':float(plddt.mean()*100),
            'plddt_0_to_100':(plddt*100).tolist(),'fraction_plddt_below50':float((plddt<0.5).mean()),
            'mean_pae_angstrom':float(pae.mean()),'confidence':confidence,
            'files':{str(p.relative_to(directory)):digest(p) for p in predicted.iterdir() if p.is_file()},
            'protein_existence':'UNKNOWN','function':'UNKNOWN'}


def run(inputs, output, cache, deadline):
    import torch
    manifest=json.loads((inputs/'manifest.json').read_text())
    output.mkdir(parents=True,exist_ok=True)
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1:
        raise RuntimeError('One working CUDA GPU required')
    save(output/'runtime.json',{'torch':torch.__version__,'cuda':torch.version.cuda,
         'gpu':torch.cuda.get_device_name(0),'python':sys.version,'started_utc':datetime.now(timezone.utc).isoformat()})
    save(output/'weights.json',weights(json.loads((inputs/'weights-manifest.json').read_text()),cache))
    jobs={j['job_id']:j for j in manifest['jobs']}
    timing_ids=manifest['timing_pilot_job_ids']
    ordered=[jobs[j] for j in timing_ids]+[j for j in manifest['jobs'] if j['job_id'] not in timing_ids]
    history=[]
    os.chdir(inputs)
    for job in ordered:
        timing=job['job_id'] in timing_ids
        if job['job_id'] in manifest.get('msa_unavailable_job_ids',[]):
            history.append({'job_id':job['job_id'],'amino_acids':job['amino_acids'],'roles':job['roles'],
                            'status':'deferred','reason':'MSA preparation unavailable; see preserved preparation ledger'})
            save(output/'jobs.json',history)
            continue
        completed=[h for h in history if h['status']=='verified']
        if timing:
            estimate=1800
        elif completed:
            upper=sorted((h for h in completed if h['amino_acids']>=job['amino_acids']),key=lambda h:h['amino_acids'])
            anchor=upper[0] if upper else max(completed,key=lambda h:h['amino_acids'])
            estimate=max(120,anchor['wall_seconds']*1.5*max(1,job['amino_acids']/anchor['amino_acids'])**3)
        else:
            estimate=None
        record={'job_id':job['job_id'],'amino_acids':job['amino_acids'],'roles':job['roles'],
                'timing_pilot':timing,'forecast_seconds':estimate}
        if estimate is None or time.time()+estimate+300>deadline:
            record.update(status='deferred',reason='No successful timing evidence or insufficient remaining bounded time')
            history.append(record);save(output/'jobs.json',history);continue
        msa=inputs/job['msa']
        if not msa.exists():
            record.update(status='deferred',reason='Required cached MSA unavailable')
            history.append(record);save(output/'jobs.json',history);continue
        target=output/job['job_id'];target.mkdir(exist_ok=True)
        argv=[str(Path(sys.executable).parent/'boltz'),'predict',job['yaml'],'--out_dir',str(target),
              '--cache',str(cache),'--model','boltz2','--accelerator','gpu','--devices','1',
              '--recycling_steps','3','--sampling_steps','200','--diffusion_samples','1',
              '--step_scale','1.5','--seed','20260919','--write_full_pae']
        record.update(argv=argv,started_utc=datetime.now(timezone.utc).isoformat(),status='running')
        history.append(record);save(output/'jobs.json',history)
        started=time.monotonic()
        try:
            limit=min(1800,deadline-time.time()-300) if timing else min(1800,max(180,estimate*2),deadline-time.time()-300)
            # GNU timeout terminates the command process group, including loader children.
            with (target/'boltz.log').open('w') as log:
                status=subprocess.run(['timeout','--signal=TERM','--kill-after=30s',str(int(limit))+'s',*argv],
                                      stdout=log,stderr=subprocess.STDOUT,check=False).returncode
            if status:
                raise RuntimeError('Boltz exited '+str(status))
            validation=validate(job,target)
            save(target/'validation.json',validation)
            record.update(status='verified',validation='validation.json')
        except Exception as error:
            record.update(status='failed',error=str(error),error_type=type(error).__name__)
        finally:
            record.update(wall_seconds=time.monotonic()-started,finished_utc=datetime.now(timezone.utc).isoformat())
            save(output/'jobs.json',history)
    save(output/'summary.json',{'status':'batch_finished','verified':sum(h['status']=='verified' for h in history),
         'failed':sum(h['status']=='failed' for h in history),'deferred':sum(h['status']=='deferred' for h in history),
         'finished_utc':datetime.now(timezone.utc).isoformat(),'deadline_epoch':deadline})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--deadline-epoch',type=float,required=True)
    args=parser.parse_args()
    run(args.inputs.resolve(),args.output.resolve(),args.cache.resolve(),args.deadline_epoch)
