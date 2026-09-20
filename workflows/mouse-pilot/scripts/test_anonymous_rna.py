"""Run a sequence-only technical control through the pilot's discovery and assessment.

No expected genes, junction coordinates or outcome labels are accepted as inputs.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

from chrna.pilot_assessment import assess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sequence-fasta', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Resume an interrupted test with the same anonymous sequence')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=args.resume)
    source = args.sequence_fasta.read_text().splitlines()
    if sum(line.startswith('>') for line in source) != 1:
        raise ValueError('Provide exactly one FASTA sequence')
    sequence = ''.join(line.strip() for line in source if not line.startswith('>')).upper()
    if not sequence or set(sequence) - set('ACGTN'):
        raise ValueError('Expected nucleotide sequence')
    query = output / 'anonymous.fastq'
    query.write_text('@query_001\n' + sequence + '\n+\n' + 'I' * len(sequence) + '\n')
    binary = root / 'runs/focused-pilot-20260919/bundle/tools/bin'
    reference = root / 'data/references/gencode_M28'
    env = {**os.environ, 'LD_LIBRARY_PATH': str(binary.parent / 'lib')}
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
        'query_id': 'query_001', 'query_length': len(sequence),
        'sequence_sha256': hashlib.sha256(sequence.encode()).hexdigest(),
        'input_role': 'anonymous_sequence_technical_control_not_observed_sample_read',
        'quality': 'Synthetic constant Q40 for FASTQ compatibility, not measured quality',
        'reference_build': 'GRCm39/GENCODE_M28',
        'reference_provenance': {p.name: json.loads(p.read_text()) for p in reference.glob('*.provenance.json')},
        'execution_difference': 'Full-genome index batched at -I100M with --split-prefix merge; 2 CPU threads. No reference restriction or threshold change.',
        'commands': [], 'expected_gene_names_supplied': False,
        'assessment_code_sha256': hashlib.sha256((root/'src/chrna/pilot_assessment.py').read_bytes()).hexdigest()}
    if args.resume:
        previous = json.loads((output/'test_provenance.json').read_text())
        if previous['sequence_sha256'] != receipt['sequence_sha256']:
            raise ValueError('Resume sequence differs')
        receipt = previous
        receipt['status'] = 'running'
        receipt.pop('error', None)
    receipt['mismatch_tags'] = 'samtools calmd against complete reference; minimap2 2.24 --MD is incompatible with --split-prefix'
    def save():
        (output / 'test_provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    def run(label, argv, stdout=None):
        if label in receipt.get('completed_stages', []):
            return
        receipt['commands'].append({'stage': label, 'argv': list(map(str, argv))})
        save()
        print(label, flush=True)
        with (output / (label + '.stderr.log')).open('w') as err:
            with (stdout or output / (label + '.stdout.log')).open('w') as out:
                subprocess.run(list(map(str, argv)), env=env, stdout=out, stderr=err, check=True, timeout=1200)
        receipt.setdefault('completed_stages', []).append(label)
        save()
    try:
        index = output / 'genome.mmi'
        run('index', [binary/'minimap2', '-x','splice','-k14','-I100M','-t2','-d', index, reference/'GRCm39.primary_assembly.genome.fa'])
        run('discovery', [binary/'minimap2','-ax','splice','-uf','-k14','--secondary=no','-G50k','-t2','--split-prefix='+str(output/'discovery_tmp'),index,query,'-o',output/'discovery.sam'])
        lines = [x for x in (output/'discovery.sam').read_text().splitlines() if not x.startswith('@')]
        receipt['supplementary_alignment_gate_passed'] = any(int(x.split('\t')[1]) & 2048 for x in lines)
        run('sort', [binary/'samtools','sort','-n','-o',output/'discovery.bam',output/'discovery.sam'])
        gtf = output / 'annotation.gtf'
        with gzip.open(reference/'gencode.vM28.annotation.gtf.gz','rb') as inp, gtf.open('wb') as out:
            import shutil
            shutil.copyfileobj(inp,out)
        run('longgf', [binary/'LongGF',output/'discovery.bam',gtf,'100','50','100','2','0','1','0'],output/'LongGF.log')
        if receipt['supplementary_alignment_gate_passed']:
            run('genome_audit', [binary/'minimap2','-ax','splice','-uf','-k14','--secondary=yes','-N50','-p0.1','-G50k','-t2','--split-prefix='+str(output/'audit_tmp'),index,query,'-o',output/'genome_audit_without_md.sam'])
            run('audit_bam',[binary/'samtools','view','-b','-o',output/'genome_audit.bam',output/'genome_audit_without_md.sam'])
            run('audit_md',[binary/'samtools','calmd',output/'genome_audit.bam',reference/'GRCm39.primary_assembly.genome.fa'],output/'split_genome_audit.sam')
            run('transcript_audit',[binary/'minimap2','-ax','map-ont','-k14','--MD','--secondary=yes','-N50','-p0.1','-t2',reference/'gencode.vM28.transcripts.fa.gz',query,'-o',output/'split_transcript_audit.sam'])
            receipt['assessment'] = assess(output, reference/'gencode.vM28.annotation.gtf.gz', output/'assessment', sample_id='anonymous_technical_control', biological_sample_id=None, rules_path=root/'docs/focused_pilot_rules.md')
        receipt['status'] = 'completed'
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
        # Generated index and decompressed annotation are disposable; retain all evidence.
        index.unlink()
        gtf.unlink()
        print(json.dumps(receipt.get('assessment',receipt),indent=2))
    except Exception as error:
        receipt['status'] = 'failed'
        receipt['error'] = str(error)
        save()
        raise

if __name__ == '__main__':
    main()
