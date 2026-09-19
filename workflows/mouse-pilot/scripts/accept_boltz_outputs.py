"""Recheck preserved predictions locally and render confidence/coordinate figures."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import gemmi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np

from boltz_worker import digest, save, validate


def compare_validations(local, remote):
    # NumPy 1.x and 2.x differ in scalar promotion (float32 mean * Python int).
    # File hashes, sequence identity and metadata remain exact; allow only tiny
    # numerical round-off in derived summaries of the same hashed arrays.
    numerical={'mean_plddt_0_to_100','plddt_0_to_100','fraction_plddt_below50','mean_pae_angstrom'}
    if {k:v for k,v in local.items() if k not in numerical}!={k:v for k,v in remote.items() if k not in numerical}:
        raise ValueError('Local structure identity, metadata or hashes differ from worker validation')
    for key in numerical:
        if np.asarray(local[key]).shape!=np.asarray(remote[key]).shape or not np.allclose(local[key],remote[key],rtol=1e-6,atol=1e-4,equal_nan=False):
            raise ValueError('Local confidence differs from worker validation: '+key)


def render(job, target, output, boundaries):
    prediction=target/('boltz_results_'+job['job_id'])/'predictions'/job['job_id']
    cif=prediction/(job['job_id']+'_model_0.cif')
    model=gemmi.read_structure(str(cif))[0][0]
    xyz=np.array([[r['CA'][0].pos.x,r['CA'][0].pos.y,r['CA'][0].pos.z] for r in model])
    plddt=np.load(prediction/f'plddt_{job["job_id"]}_model_0.npz')['plddt'].squeeze()*100
    pae=np.load(prediction/f'pae_{job["job_id"]}_model_0.npz')['pae'].squeeze()
    roles=job['roles']
    title=' / '.join(r.get('gene_name_5p','Gsdmd')+' → '+r.get('gene_name_3p','Tmem106a') for r in roles)
    if any(r['role']=='published_architecture_reference_control' for r in roles):title+=' (separate control)'
    fig=plt.figure(figsize=(12,7),layout='constrained')
    grid=fig.add_gridspec(2,2)
    ax=fig.add_subplot(grid[:,0],projection='3d')
    segments=np.stack([xyz[:-1],xyz[1:]],axis=1)
    lines=Line3DCollection(segments,cmap='viridis',norm=matplotlib.colors.Normalize(0,100),linewidth=2)
    lines.set_array((plddt[:-1]+plddt[1:])/2);ax.add_collection3d(lines)
    center=(xyz.min(axis=0)+xyz.max(axis=0))/2;radius=max(np.ptp(xyz,axis=0).max()/2,1)
    ax.set_xlim(center[0]-radius,center[0]+radius);ax.set_ylim(center[1]-radius,center[1]+radius);ax.set_zlim(center[2]-radius,center[2]+radius)
    ax.set_box_aspect((1,1,1));ax.set_axis_off();ax.set_title('Predicted Cα trace; color = pLDDT')
    fig.colorbar(lines,ax=ax,shrink=.5,label='pLDDT (0–100)')
    confidence=fig.add_subplot(grid[0,1]);confidence.plot(np.arange(1,len(plddt)+1),plddt,color='#216078',linewidth=1)
    confidence.set(xlim=(1,len(plddt)),ylim=(0,100),xlabel='Residue',ylabel='pLDDT (0–100)')
    confidence.axhline(50,color='gray',linestyle=':',linewidth=.8)
    error=fig.add_subplot(grid[1,1]);picture=error.imshow(pae,origin='lower',extent=(.5,len(plddt)+.5,.5,len(plddt)+.5),vmin=0,vmax=max(30,float(pae.max())),cmap='magma_r')
    error.set(xlabel='Residue index (column)',ylabel='Residue index (row)',title='Predicted aligned error')
    fig.colorbar(picture,ax=error,label='Å')
    for boundary in boundaries:
        confidence.axvline(boundary+.5,color='#ba3b54',linestyle='--',linewidth=.8)
        error.axvline(boundary+.5,color='#ba3b54',linestyle='--',linewidth=.8)
        error.axhline(boundary+.5,color='#ba3b54',linestyle='--',linewidth=.8)
    fig.suptitle(title+'\nOne Boltz-2 sample; expression and function UNKNOWN',fontsize=13)
    png=output/(job['job_id']+'.png');fig.savefig(png,dpi=160);plt.close(fig)
    return png


def main(run):
    active=run/'active-folding-attempt.json'
    attempt=run/json.loads(active.read_text())['attempt_directory'] if active.exists() else run/'folding-worker'
    if not attempt.resolve().is_relative_to(run.resolve()):raise ValueError('Unexpected worker attempt path')
    inputs=run/'fold-inputs';worker=attempt/'worker-outputs/predictions'
    manifest=json.loads((inputs/'manifest.json').read_text())
    freeze=run/'selection/freeze.json'
    if digest(freeze)!=manifest['selection_freeze_sha256']:raise ValueError('Selection freeze changed')
    for name,sha in json.loads(freeze.read_text())['outputs'].items():
        if digest(freeze.parent/name)!=sha:raise ValueError('Frozen output changed: '+name)
    history=json.loads((worker/'jobs.json').read_text())
    jobs={j['job_id']:j for j in manifest['jobs']}
    if len(history)!=len(jobs) or {h['job_id'] for h in history}!=set(jobs):raise ValueError('Incomplete or duplicated worker job ledger')
    selected={h['protein_id']:h for h in json.loads((run/'selection/selection.json').read_text())['selected']}
    reconstructions={(r['junction_id'],r['read_id']):r for r in json.loads((run/'orfs/reconstructions.json').read_text())}
    out=run/'structures';out.mkdir(exist_ok=True);results=[]
    for record in history:
        job=jobs[record['job_id']];target=worker/job['job_id']
        result={**record,'roles':job['roles'],'sequence_sha256':job['sequence_sha256']}
        if record['status']=='verified':
            remote=json.loads((target/'validation.json').read_text())
            for relative,sha in remote['files'].items():
                path=target/relative
                if not path.resolve().is_relative_to(target.resolve()) or digest(path)!=sha:raise ValueError('Copied prediction hash mismatch')
            checked=validate(job,target)
            compare_validations(checked,remote)
            boundaries=[73] if any(r['role']=='published_architecture_reference_control' for r in job['roles']) else []
            if job['job_id'] in selected:
                h=selected[job['job_id']];r=reconstructions[(h['junction_id'],h['read_id'])]
                boundaries=sorted({(b-h['orf']['start'])/3 for b in r['reference_assisted_junction_interval']})
            figure=render(job,target,out,boundaries)
            confidence=out/(job['job_id']+'_confidence.csv')
            with confidence.open('w',newline='') as stream:
                writer=csv.writer(stream);writer.writerow(['residue_1based','amino_acid','plddt_0_to_100'])
                writer.writerows((i,aa,score) for i,(aa,score) in enumerate(zip(job['sequence'],checked['plddt_0_to_100']),1))
            result.update(validation=checked,figure=str(figure.relative_to(run)),confidence_csv=str(confidence.relative_to(run)),
                          prediction_directory=str(target.relative_to(run)),junction_residue_offsets=boundaries)
        results.append(result)
    summary={'status':'preserved_predictions_locally_verified','created_utc':datetime.now(timezone.utc).isoformat(),
             'selection_freeze_sha256':digest(freeze),'worker_jobs_sha256':digest(worker/'jobs.json'),
             'verified':sum(r['status']=='verified' for r in results),'failed':sum(r['status']=='failed' for r in results),
             'deferred':sum(r['status']=='deferred' for r in results),'jobs':results,
             'numeric_summary_comparison':{'rtol':1e-6,'atol':1e-4,'reason':'NumPy scalar-promotion differences; raw file hashes and sequences checked exactly'},
             'interpretation':'Prediction confidence only; protein expression, function and author-coordinate agreement UNKNOWN.'}
    save(out/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='jobs'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=Path('runs/focused-pilot-20260919'))
    main(parser.parse_args().run.resolve())
