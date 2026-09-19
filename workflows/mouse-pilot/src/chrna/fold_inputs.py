"""Prepare bounded Boltz jobs from a verified frozen shortlist and separate control."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


def prepare(run, output):
    freeze_dir = run/'selection'
    freeze = json.loads((freeze_dir/'freeze.json').read_text())
    if freeze['status'] != 'frozen':
        raise ValueError('Folding requires a frozen selection, not a preview')
    for name, digest in freeze['outputs'].items():
        if hashlib.sha256((freeze_dir/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen selection artifact changed: '+name)
    selection = json.loads((freeze_dir/'selection.json').read_text())
    if len(selection['selected']) > 10:
        raise ValueError('Recovered protein count exceeds focused scope')
    jobs = {}
    def add(sequence, role, provenance):
        if not sequence or set(sequence)-set('ACDEFGHIKLMNPQRSTVWY'):
            raise ValueError('Unresolved amino-acid sequence')
        digest = hashlib.sha256(sequence.encode()).hexdigest()
        job = jobs.setdefault(digest, dict(job_id='protein_'+digest, sequence_sha256=digest,
                              sequence=sequence, amino_acids=len(sequence), roles=[]))
        job['roles'].append({'role':role, **provenance})
    for h in selection['selected']:
        add(h['sequence'], 'pilot_recovered_reference_assisted',
            {'junction_id':h['junction_id'],'selection_order':h['selection_order'],
             'gene_name_5p':h['gene_name_5p'],'gene_name_3p':h['gene_name_3p']})
    control_dir = run/'published-control'
    control = json.loads((control_dir/'provenance.json').read_text())
    control_sequence = ''.join(line for line in (control_dir/'published_architecture_control.fasta').read_text().splitlines() if not line.startswith('>'))
    if hashlib.sha256(control_sequence.encode()).hexdigest() != control['protein_sha256']:
        raise ValueError('Published control sequence changed')
    add(control_sequence, 'published_architecture_reference_control',
        {'not_de_novo_recovered':True,'provenance_status':control['status']})
    output.mkdir(parents=True, exist_ok=False)
    (output/'msas').mkdir()
    ordered = sorted(jobs.values(), key=lambda j:(j['amino_acids'],j['job_id']))
    pilot_indices = sorted({0,len(ordered)//2,len(ordered)-1})
    pilot_ids = [ordered[i]['job_id'] for i in pilot_indices]
    for job in ordered:
        job_id = job['job_id']
        job['stage'] = 'timing_pilot' if job_id in pilot_ids else 'production_after_timing_review'
        fasta = output/(job_id+'.fasta')
        fasta.write_text(f'>{job_id}\n{job["sequence"]}\n')
        job['fasta'] = fasta.name
        msa = output/'msas'/(job_id+'.a3m')
        if job['sequence_sha256']==control['protein_sha256'] and (control_dir/'msa/msa.json').exists():
            receipt = json.loads((control_dir/'msa/msa.json').read_text())
            source = control_dir/'msa/alignment.a3m'
            if receipt['sequence_sha256'] != job['sequence_sha256'] or hashlib.sha256(source.read_bytes()).hexdigest()!=receipt['a3m_sha256']:
                raise ValueError('Control MSA cache mismatch')
            shutil.copyfile(source, msa)
            shutil.copyfile(control_dir/'msa/msa.json', msa.with_suffix('.json'))
        # JSON is valid YAML. Resolve the relative MSA under the job working directory.
        config = {'version':1,'sequences':[{'protein':{'id':'A','sequence':job['sequence'],
                                                        'msa':'msas/'+msa.name}}]}
        (output/(job_id+'.yaml')).write_text(json.dumps(config,indent=2)+'\n')
        job['yaml'] = job_id+'.yaml'
        job['msa'] = 'msas/'+msa.name
    manifest = {'status':'inputs_prepared_not_inferred','created_utc':datetime.now(timezone.utc).isoformat(),
                'selection_freeze_sha256':hashlib.sha256((freeze_dir/'freeze.json').read_bytes()).hexdigest(),
                'published_control_provenance_sha256':hashlib.sha256((control_dir/'provenance.json').read_bytes()).hexdigest(),
                'jobs':ordered,'timing_pilot_job_ids':pilot_ids,
                'settings':{'model':'boltz2','boltz_version':'2.2.1','recycling_steps':3,'sampling_steps':200,
                            'diffusion_samples':1,'step_scale':1.5,'seed':20260919,'write_full_pae':True},
                'repeat_policy':'No repeat predictions scheduled; requires separate prespecification and remaining-time review.',
                'production_policy':'Measure the three available representative lengths before scheduling remaining production jobs.',
                'protein_existence':'UNKNOWN','function':'UNKNOWN'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'jobs':len(ordered),'timing_pilot':pilot_ids,'output':str(output)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=Path('runs/focused-pilot-20260919'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.run,args.output),indent=2))


if __name__=='__main__':
    main()
