"""Annotate frozen pilot RNA paths; never changes ranking or selection.

Internal intervals are zero-based half-open. Exon numbering is transcript-specific.
The display transcript maximizes covered reference bases, then matched N gaps;
this is a deterministic annotation choice, not a resolved biological isoform.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from chrna.pilot_orfs import CODONS, IndexedFasta, revcomp


def attributes(text):
    return {k: a if a else b for k, a, b in
            re.findall(r'(\w+)\s+(?:"([^"]*)"|([^;\s]+))\s*;', text)}


def reference_blocks(alignment):
    """Reference-assisted M/= /X/D bases, separated only by skipped N spans."""
    pos = start = alignment['start']
    blocks = []
    for count, op in re.findall(r'(\d+)([MIDNSHP=X])', alignment['cigar']):
        count = int(count)
        if op in 'MD=X':
            pos += count
        elif op == 'N':
            if pos > start:
                blocks.append((start, pos))
            pos += count
            start = pos
    if pos > start:
        blocks.append((start, pos))
    assert pos == alignment['end']
    return blocks[::-1] if alignment['strand'] == '-' else blocks


def read_annotation(path, wanted):
    genes = defaultdict(dict)
    with gzip.open(path, 'rt') as stream:
        for row, line in enumerate(stream, 1):
            if line.startswith('#'):
                continue
            f = line.rstrip().split('\t')
            if f[2] != 'exon':
                continue
            a = attributes(f[8])
            if a.get('gene_id') not in wanted:
                continue
            tx = genes[a['gene_id']].setdefault(a['transcript_id'], {
                'id': a['transcript_id'], 'name': a.get('transcript_name', a['transcript_id']),
                'gene': a['gene_name'], 'chromosome': f[0], 'strand': f[6],
                'biotype': a['gene_type'], 'exons': []})
            tx['exons'].append({'start': int(f[3]) - 1, 'end': int(f[4]),
                                'number': int(a['exon_number']), 'id': a['exon_id'],
                                'source_row': row})
    for transcripts in genes.values():
        for tx in transcripts.values():
            tx['exons'].sort(key=lambda e: e['number'])
    return genes


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def annotate_transcript(tx, blocks):
    segments = []
    offset = 0
    for index, (start, end) in enumerate(blocks):
        cuts = sorted({start, end} | {max(start, min(end, e[k])) for e in tx['exons'] for k in ('start', 'end')})
        parts = list(zip(cuts, cuts[1:]))
        if tx['strand'] == '-':
            parts.reverse()
        for lo, hi in parts:
            if lo == hi:
                continue
            matches = [e for e in tx['exons'] if e['start'] <= lo and hi <= e['end']]
            assert len(matches) <= 1, 'Overlapping exons within one transcript'
            exon = matches[0] if matches else None
            inside = min(e['start'] for e in tx['exons']) <= lo and hi <= max(e['end'] for e in tx['exons'])
            segment = {'start': lo, 'end': hi, 'rna_start': offset, 'rna_end': offset + hi - lo,
                       'block': index + 1, 'kind': 'exon' if exon else 'intron' if inside else 'outside',
                       'number': exon['number'] if exon else None,
                       'exon_id': exon['id'] if exon else None,
                       'source_row': exon['source_row'] if exon else None,
                       'partial': bool(exon and (lo != exon['start'] or hi != exon['end']))}
            segments.append(segment)
            offset += hi - lo
    gaps = set()
    sorted_exons = sorted(tx['exons'], key=lambda e: e['start'])
    for left, right in zip(sorted_exons, sorted_exons[1:]):
        gaps.add((left['end'], right['start']))
    genomic_blocks = sorted(blocks)
    matched_gaps = sum((a[1], b[0]) in gaps for a, b in zip(genomic_blocks, genomic_blocks[1:]))
    covered = sum(s['end'] - s['start'] for s in segments if s['kind'] == 'exon')
    return {**tx, 'segments': segments, 'covered_nt': covered, 'projected_nt': offset,
            'nonexonic_nt': offset - covered, 'matched_splice_gaps': matched_gaps,
            'alignment_splice_gaps': len(blocks) - 1}


def arm_data(decision, side, annotation):
    short, key = ('5p', 'left') if side == 0 else ('3p', 'right')
    a = decision[key + '_alignment']
    blocks = reference_blocks(a)
    choices = [annotate_transcript(tx, blocks) for tx in annotation[decision['gene_' + short]].values()
               if tx['strand'] == a['strand'] and tx['chromosome'] == a['target']]
    choices.sort(key=lambda t: (-t['covered_nt'], -t['matched_splice_gaps'], t['id']))
    assert choices
    best = choices[0]
    tied = sum((t['covered_nt'], t['matched_splice_gaps']) == (best['covered_nt'], best['matched_splice_gaps']) for t in choices)
    boundary = decision['boundary_' + short]
    # A junction is between bases: inspect the contributed base on each arm.
    adjacent_base = boundary - 1 if (side == 0) == (a['strand'] == '+') else boundary
    for t in choices:
        hits = [e for e in t['exons'] if e['start'] <= adjacent_base < e['end']]
        edges = [e['end'] if (side == 0) == (a['strand'] == '+') else e['start'] for e in t['exons']]
        t['boundary_exons'] = [e['number'] for e in hits]
        t['nearest_edge_delta_nt'] = min((boundary - e for e in edges), key=abs)
    return {'gene': decision['gene_name_' + short], 'gene_id': decision['gene_' + short],
            'chromosome': a['target'], 'strand': a['strand'], 'biotype': decision['biotype_' + short],
            'boundary_zero_based': boundary, 'adjacent_base_one_based': adjacent_base + 1,
            'blocks': blocks, 'choices': choices, 'equally_scored_transcripts': tied}


def projected_sequence(alignment, genome, corrections, arm):
    blocks = reference_blocks(alignment)
    seq = ''
    variants = {c['reference_position']: c['observed'] for c in corrections
                if c['arm'] == arm and c['action'] == 'retain_high_quality_observed_substitution'}
    for start, end in blocks:
        chars = list(genome.fetch(alignment['target'], start, end))
        for pos, base in variants.items():
            if start <= pos < end:
                chars[pos - start] = base
        part = ''.join(chars)
        seq += revcomp(part) if alignment['strand'] == '-' else part
    return seq


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root=ROOT):
    run = root / 'runs/focused-pilot-20260919'
    paths = {'selection': run/'selection/selection.json', 'decisions': run/'selection/read_decisions.json',
             'reconstructions': run/'orfs/reconstructions.json', 'annotation': root/'data/references/gencode_M28/gencode.vM28.annotation.gtf.gz'}
    selected = json.loads(paths['selection'].read_text())['selected']
    decisions = {(r['junction_id'], r['read_id']): r for r in json.loads(paths['decisions'].read_text())}
    reconstructed = {(r['junction_id'], r['read_id']): r for r in json.loads(paths['reconstructions'].read_text())}
    wanted = {decisions[(s['junction_id'], s['read_id'])]['gene_' + side] for s in selected for side in ('5p', '3p')}
    annotation = read_annotation(paths['annotation'], wanted)
    genome = IndexedFasta(root/'data/references/gencode_M28/GRCm39.primary_assembly.genome.fa')
    results = []
    for s in selected:
        d = decisions[(s['junction_id'], s['read_id'])]
        rec = reconstructed[(s['junction_id'], s['read_id'])]
        arms = [arm_data(d, i, annotation) for i in range(2)]
        left = projected_sequence(d['left_alignment'], genome, rec['corrections_and_variants'], 'left')
        right = projected_sequence(d['right_alignment'], genome, rec['corrections_and_variants'], 'right')
        gap = d['comparison']['query_gap']
        if gap < 0:
            assert left[gap:] == right[:-gap]
            rna = left + right[-gap:]
            join = [len(left) + gap, len(left)]
        elif gap > 0:
            insert = rec['observed_rna'][d['left_alignment']['qend']:d['right_alignment']['qstart']]
            rna = left + insert + right
            join = [len(left), len(left) + gap]
        else:
            rna = left + right
            join = [len(left), len(left)]
        assert rna == rec['reference_assisted_rna'], 'Replayed RNA differs from frozen reconstruction'
        assert join == rec['reference_assisted_junction_interval']
        start, stop = s['orf']['start'], s['orf']['stop_start']
        protein = ''.join(CODONS[rna[k:k+3]] for k in range(start, stop, 3))
        assert protein == s['sequence']
        assert digest_string(protein) == s['sequence_sha256']
        results.append({'name': s['gene_name_5p'] + ' → ' + s['gene_name_3p'],
                        'order': s['selection_order'], 'protein_id': s['protein_id'], 'read_id': s['read_id'],
                        'junction_id': s['junction_id'], 'read_count': len(s['protein_supporting_read_ids']),
                        'sequence_source': s['sequence_source'], 'length_nt': len(rna), 'length_aa': len(protein),
                        'orf': s['orf'], 'junction': join, 'query_gap': gap, 'arms': arms,
                        'correction_events': len(rec['corrections_and_variants']),
                        'rna_replay_verified': True, 'protein_translation_verified': True})
    return {'reference': 'GRCm39 / GENCODE M28', 'created_utc': datetime.now(timezone.utc).isoformat(),
            'coordinate_convention': 'Internal 0-based half-open; displayed genomic bases 1-based inclusive; boundaries between bases.',
            'transcript_choice': 'Maximum reference-assisted exonic base coverage, then exact CIGAR-N gap matches, then transcript ID; illustrative, not inferred isoform.',
            'sources': {k: {'path': str(v.relative_to(root)), 'sha256': digest(v)} for k, v in paths.items()},
            'candidates': results}


def digest_string(value):
    return hashlib.sha256(value.encode()).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'reports/exon_annotations_20260920.json')
    parser.add_argument('--template', type=Path)
    parser.add_argument('--view', type=Path)
    args = parser.parse_args()
    data = build()
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    if args.template or args.view:
        assert args.template and args.view
        fragment = args.template.read_text().replace('__ANNOTATION_DATA__', json.dumps(data, separators=(',', ':')))
        assert '__ANNOTATION_DATA__' not in fragment and len(fragment.encode()) < 1_000_000
        args.view.write_text(fragment)
    for c in data['candidates']:
        print(c['name'], 'ORF', c['orf']['start'], c['orf']['stop_start'], 'join', c['junction'])
        for a in c['arms']:
            t = a['choices'][0]
            print(' ', a['gene'], t['name'], t['id'], 'exons', [s['number'] for s in t['segments'] if s['number']],
                  'nonexonic_nt', t['nonexonic_nt'], 'best_ties', a['equally_scored_transcripts'], 'edge_delta', t['nearest_edge_delta_nt'])
