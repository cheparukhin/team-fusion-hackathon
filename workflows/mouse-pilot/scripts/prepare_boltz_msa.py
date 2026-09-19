"""Cache a public sequence's MSA using the hash-verified Boltz 2.2.1 client.

Invoke with an external timeout; the upstream client polls a remote service.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fasta', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    preparation = Path('runs/focused-pilot-20260919/boltz-preparation')
    metadata = json.loads((preparation/'pypi-version.json').read_text())
    dist = next(d for d in metadata['distributions'] if d['packagetype']=='bdist_wheel')
    wheel = preparation/dist['filename']
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == dist['digests']['sha256']
    code = preparation/'wheel_boltz_data_msa_mmseqs2.py'
    with zipfile.ZipFile(wheel) as archive:
        assert code.read_bytes() == archive.read('boltz/data/msa/mmseqs2.py')
    spec = importlib.util.spec_from_file_location('boltz_pinned_msa_client', code)
    client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client)
    fasta = args.fasta.read_text().splitlines()
    assert sum(line.startswith('>') for line in fasta)==1, 'One sequence per cached MSA'
    sequence = ''.join(line for line in fasta if not line.startswith('>')).strip()
    assert sequence and not set(sequence)-set('ACDEFGHIKLMNPQRSTVWY')
    args.output.mkdir(parents=True, exist_ok=True)
    receipt_path = args.output/'msa.json'
    digest = hashlib.sha256(sequence.encode()).hexdigest()
    if receipt_path.exists():
        old = json.loads(receipt_path.read_text())
        assert old['sequence_sha256']==digest, 'Cannot reuse cache for another sequence'
        assert hashlib.sha256((args.output/'alignment.a3m').read_bytes()).hexdigest()==old['a3m_sha256']
        print(json.dumps(old, indent=2));return
    started = time.monotonic()
    msa = client.run_mmseqs2(sequence, prefix=str(args.output/digest), use_env=True, use_filter=True)[0]
    rows = []
    for line in msa.splitlines():
        if line.startswith('>'):
            rows.append('')
        elif line and not line.startswith('#'):
            rows[-1] += line
    assert rows and rows[0]==sequence, 'MSA query does not match the requested protein'
    aligned = [''.join(c for c in row if not c.islower()) for row in rows]
    assert all(len(row)==len(sequence) for row in aligned), 'MSA aligned widths differ'
    (args.output/'alignment.a3m').write_text(msa)
    receipt = {'status':'cached', 'sequence_sha256':digest,
               'a3m_sha256':hashlib.sha256(msa.encode()).hexdigest(), 'rows':len(rows),
               'aligned_non_gap_depth':[sum(row[i] not in '-.' for row in aligned) for i in range(len(sequence))],
               'wall_seconds':time.monotonic()-started,'finished_utc':datetime.now(timezone.utc).isoformat(),
               'server':'https://api.colabfold.com','client_version':'boltz 2.2.1',
               'client_wheel_sha256':dist['digests']['sha256'],
               'input_fasta':str(args.fasta),'settings':{'use_env':True,'use_filter':True,'use_pairing':False}}
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='aligned_non_gap_depth'},indent=2))


if __name__=='__main__':
    main()
