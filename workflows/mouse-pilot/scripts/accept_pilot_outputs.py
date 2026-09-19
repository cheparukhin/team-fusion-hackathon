"""Validate a completed preserved pilot before exposing it to downstream rules."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'runs/focused-pilot-20260919'


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def accept(attempt):
    controller=json.loads((attempt/'worker-controller.json').read_text())
    shutdown=json.loads((attempt/'shutdown-confirmed.json').read_text())
    if controller['status']!='succeeded' or shutdown['status']!='STOPPED':
        raise ValueError('Pilot attempt must have succeeded and its worker must be stopped')
    candidates=list((attempt/'worker-outputs').rglob('exit_code.txt'))
    if len(candidates)!=1:raise ValueError('Expected one preserved worker output directory')
    directory=candidates[0].parent
    if candidates[0].read_text().strip()!='0':raise ValueError('Worker did not exit successfully')
    verified={}
    for line in (directory/'core_output.sha256').read_text().splitlines():
        expected,name=line.split(maxsplit=1)
        path=directory/Path(name.strip()).name
        actual=sha256(path)
        if actual!=expected:raise ValueError('Transferred core output checksum mismatch: '+path.name)
        verified[path.name]=actual
    flagstat=(directory/'flagstat.txt').read_text()
    primary=re.search(r'^(\d+) \+ (\d+) primary$',flagstat,re.M)
    if primary is None or sum(map(int,primary.groups()))!=2238871:
        raise ValueError('Full pilot primary-record count is not 2,238,871')
    subprocess.run([str(ROOT/'.tools/envs/typhon/bin/samtools'),'quickcheck','-v',str(directory/'pilot.name.bam')],check=True)
    expected_ids=set((directory/'split_read_ids.txt').read_text().splitlines())
    receipt=json.loads((directory/'split_read_extraction.json').read_text())
    if receipt['reads']!=len(expected_ids):raise ValueError('Split-read extraction count mismatch')
    names=[]
    with (directory/'split_reads.fastq').open() as source:
        while True:
            row=[source.readline().rstrip('\n') for _ in range(4)]
            if not row[0]:break
            if not row[0].startswith('@') or not row[2].startswith('+') or len(row[1])!=len(row[3]):
                raise ValueError('Incomplete or malformed split-read FASTQ')
            names.append(row[0][1:].split()[0])
    if len(names)!=len(expected_ids) or set(names)!=expected_ids:
        raise ValueError('Split-read FASTQ identities differ from extraction list')
    for name in ('split_genome_audit.sam','split_transcript_audit.sam'):
        groups=[];previous=None
        with (directory/name).open() as source:
            for line in source:
                if line.startswith('@'):continue
                rid=line.split('\t',1)[0]
                if rid!=previous:groups.append(rid);previous=rid
        if groups!=names:raise ValueError('Audit SAM query order/completeness mismatch: '+name)
        verified[name]=sha256(directory/name)
    record={'status':'validated_complete_pilot','validated_utc':datetime.now(timezone.utc).isoformat(),
            'primary_records':2238871,'split_reads':len(names),'output_directory':str(directory),
            'attempt':str(attempt),'verified_sha256':verified,'worker_stopped':True,
            'scope':'One biological sample; minimap2/LongGF and supplementary-read mapping audit, not caller consensus.'}
    target=BASE/'discovery-validation.json'
    temporary=target.with_suffix('.json.partial');temporary.write_text(json.dumps(record,indent=2)+'\n');temporary.replace(target)
    link=BASE/'discovery'
    if link.exists() or link.is_symlink():
        if link.resolve()!=directory.resolve():raise ValueError('Discovery path already refers to another result')
    else:link.symlink_to(os.path.relpath(directory,link.parent),target_is_directory=True)
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(accept(args.attempt.resolve()),indent=2))
