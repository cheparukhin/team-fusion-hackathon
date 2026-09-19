"""Create a local random-access derivative of the already validated genome."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compressed',type=Path,required=True)
p.add_argument('--samtools',type=Path,required=True)
a=p.parse_args()
target=a.compressed.with_suffix('')
receipt=Path(str(target)+'.derivative.json')
source=json.loads(Path(str(a.compressed)+'.provenance.json').read_text())
if receipt.exists() and target.exists() and Path(str(target)+'.fai').exists():
    prior=json.loads(receipt.read_text())
    assert prior['compressed_sha256']==source['sha256']
    assert prior['bytes']==target.stat().st_size
    print(json.dumps({'status':'reused','receipt':str(receipt)}))
else:
    h=hashlib.sha256();size=0
    temporary=Path(str(target)+'.partial')
    with gzip.open(a.compressed,'rb') as src, temporary.open('wb') as out:
        for chunk in iter(lambda:src.read(4*1024*1024),b''):
            out.write(chunk);h.update(chunk);size+=len(chunk)
    temporary.replace(target)
    subprocess.run([str(a.samtools),'faidx',str(target)],check=True)
    receipt.write_text(json.dumps({'status':'indexed','compressed_sha256':source['sha256'],
        'fasta_sha256':h.hexdigest(),'bytes':size,'fai_sha256':hashlib.sha256(Path(str(target)+'.fai').read_bytes()).hexdigest(),
        'purpose':'Random-access reference-assisted sequence reconstruction; no new biological analysis'},indent=2)+'\n')
    print(receipt.read_text())
