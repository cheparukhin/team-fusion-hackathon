"""Package the already verified caller binaries with their locked shared libraries."""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tarfile

root = pathlib.Path(__file__).resolve().parents[1]
prefix = root / '.tools/envs/typhon'
bundle = root / 'runs/focused-pilot-20260919/bundle'
bundle.mkdir(parents=True, exist_ok=True)
files = {}
for name in ('minimap2', 'samtools', 'LongGF'):
    binary = prefix / 'bin' / name
    files['tools/bin/' + name] = binary
    result = subprocess.run(['ldd', str(binary)], capture_output=True, text=True, check=True)
    if 'not found' in result.stdout:
        raise RuntimeError(result.stdout)
    for library in re.findall(r'=> (/\S+)', result.stdout):
        p = pathlib.Path(library)
        if p.is_relative_to(prefix):
            files['tools/lib/' + p.name] = p
hashes = []
for name, source in sorted(files.items()):
    target = bundle / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    hashes.append(hashlib.sha256(target.read_bytes()).hexdigest() + '  ' + name)
(bundle/'tools.sha256').write_text('\n'.join(hashes)+'\n')
shutil.copy2(root/'scripts/pilot_discovery_worker.sh', bundle/'worker.sh')
validation = json.loads((root/'runs/pilot-20260919/intake_validation.json').read_text())
input_hashes = [validation['fastq_sha256']+'  inputs/SRR28984805.fastq']
for name in ('GRCm39.primary_assembly.genome.fa.gz', 'gencode.vM28.annotation.gtf.gz', 'gencode.vM28.transcripts.fa.gz'):
    receipt = json.loads((root/'data/references/gencode_M28'/f'{name}.provenance.json').read_text())
    input_hashes.append(receipt['sha256']+'  inputs/'+name)
(bundle/'inputs.sha256').write_text('\n'.join(input_hashes)+'\n')
with tarfile.open(bundle.parent/'tools-and-script.tar.gz', 'w:gz') as out:
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            out.add(path, arcname=str(path.relative_to(bundle)), recursive=False)
print(json.dumps({'bundle':str(bundle.parent/'tools-and-script.tar.gz'),'binaries':3,'locked_libraries':len(files)-3}))
