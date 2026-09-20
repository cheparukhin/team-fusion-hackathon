"""Audit reference-assisted chRNA ORFs without asserting observed full exon chains.

Run: .venv/bin/python scripts/structure_campaign/reconstruct.py
Only standard-library modules are needed. Source inputs are never modified.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import itertools
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASES = 'TCAG'
AAS = 'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
CODE = dict(zip((''.join(c) for c in itertools.product(BASES, repeat=3)), AAS))
STOPS = {'TAA', 'TAG', 'TGA'}
TIERS = ['conditional_consensus', 'conditional_annotated_start', 'alternative_start_sensitivity']


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_tsv(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write_tsv(path, rows, fields=None):
    with Path(path).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def write_fasta(path, records):
    with Path(path).open('w') as f:
        for identifier, sequence in records:
            f.write(f'>{identifier}\n')
            for offset in range(0, len(sequence), 80):
                f.write(sequence[offset:offset + 80] + '\n')


def attrs(text):
    result = defaultdict(list)
    for field in text.split(';'):
        if field.strip():
            key, value = field.strip().split(' ', 1)
            result[key].append(value.strip('"'))
    return result


def tx_offset(model, genomic_base):
    """1-based inclusive genomic base -> 0-based transcript nucleotide."""
    offset = 0
    for exon in model['exons']:
        if exon['start'] <= genomic_base <= exon['end']:
            return offset + (genomic_base - exon['start'] if model['strand'] == '+' else exon['end'] - genomic_base)
        offset += exon['end'] - exon['start'] + 1
    raise ValueError(f'base {genomic_base} outside transcript exons')


def genomic_base(model, offset):
    if offset < 0:
        raise ValueError('negative transcript offset')
    for exon in model['exons']:
        size = exon['end'] - exon['start'] + 1
        if offset < size:
            return exon['start'] + offset if model['strand'] == '+' else exon['end'] - offset
        offset -= size
    raise ValueError('transcript offset out of bounds')


def load_transcripts(gtf, fasta, wanted):
    models = {t: {'transcript_id': t, 'exons': [], 'start_bases': [], 'cds_genomic_intervals': [], 'tags': []} for t in wanted}
    with gzip.open(gtf, 'rt') as f:
        for line in f:
            if line.startswith('#'):
                continue
            c = line.rstrip().split('\t')
            if c[2] not in {'transcript', 'exon', 'start_codon', 'CDS'}:
                continue
            a = attrs(c[8]); tid = a.get('transcript_id', [None])[0]
            if tid not in models:
                continue
            m = models[tid]
            m.update(chrom=c[0], strand=c[6], gene_id=a['gene_id'][0], gene_name=a['gene_name'][0], transcript_type=a.get('transcript_type', ['unknown'])[0])
            if c[2] == 'exon':
                m['exons'].append(dict(start=int(c[3]), end=int(c[4]), exon_number=int(a['exon_number'][0])))
            elif c[2] == 'start_codon':
                m['start_bases'].extend(range(int(c[3]), int(c[4]) + 1))
            elif c[2] == 'CDS':
                m['cds_genomic_intervals'].append((int(c[3]), int(c[4])))
            else:
                m['tags'] = a.get('tag', [])
    current = None
    with gzip.open(fasta, 'rt') as f:
        for line in f:
            if line.startswith('>'):
                current = line[1:].split('|')[0]
                if current in models:
                    models[current]['sequence'] = ''
            elif current in models:
                models[current]['sequence'] += line.strip().upper()
    for tid, m in models.items():
        m['exons'].sort(key=lambda e: e['exon_number'])
        assert len(m['sequence']) == sum(e['end'] - e['start'] + 1 for e in m['exons']), tid
        starts = sorted(tx_offset(m, p) for p in m['start_bases'])
        m['annotated_start'] = starts[0] if len(starts) == 3 and starts == list(range(starts[0], starts[0] + 3)) and m['sequence'][starts[0]:starts[0] + 3] == 'ATG' and 'cds_start_NF' not in m['tags'] else None
        m['cds_intervals'] = sorted((min(tx_offset(m, lo), tx_offset(m, hi)), max(tx_offset(m, lo), tx_offset(m, hi)) + 1) for lo, hi in m.pop('cds_genomic_intervals'))
        m.pop('start_bases')
    return models


def orf_at(sequence, start):
    """Complete ATG -> first in-frame stop; stop is excluded from peptide."""
    if sequence[start:start + 3] != 'ATG':
        return None
    peptide = []
    for pos in range(start, len(sequence) - 2, 3):
        codon = sequence[pos:pos + 3]
        if codon not in CODE:
            return None
        if codon in STOPS:
            return dict(start_0based=start, stop_start_0based=pos, coding_nt=pos - start, sequence=''.join(peptide))
        peptide.append(CODE[codon])
    return None


def crossing_orfs(sequence, junction, min_coding_nt=90):
    results = []
    for start in range(junction):
        if sequence[start:start + 3] != 'ATG':
            continue
        orf = orf_at(sequence, start)
        if orf and orf['coding_nt'] >= min_coding_nt and start < junction < orf['stop_start_0based']:
            results.append(orf)
    return results


def reconstruct(left, right, donor_base, acceptor_base, probe):
    a = tx_offset(left, donor_base)
    b = tx_offset(right, acceptor_base)
    sequence = left['sequence'][:a + 1] + right['sequence'][b:]
    junction = a + 1
    if sequence[junction - 60:junction + 60] != probe:
        raise ValueError('reconstructed sequence does not exactly reproduce 120-nt probe')
    donor_boundary = any(donor_base == e['end' if left['strand'] == '+' else 'start'] for e in left['exons'])
    acceptor_boundary = any(acceptor_base == e['start' if right['strand'] == '+' else 'end'] for e in right['exons'])
    return sequence, junction, b, donor_boundary and acceptor_boundary


def source_residues(orf, junction, acceptor_offset, left, right, parent_orfs):
    """Return exact triplet provenance and canonical protein correspondence."""
    for index, aa in enumerate(orf['sequence']):
        positions = list(range(orf['start_0based'] + 3 * index, orf['start_0based'] + 3 * index + 3))
        mapped = []
        for p in positions:
            side = 'a' if p < junction else 'b'
            model = left if side == 'a' else right
            offset = p if side == 'a' else acceptor_offset + p - junction
            mapped.append((side, model, offset, genomic_base(model, offset)))
        sides = {v[0] for v in mapped}
        canonical_index = ''
        if len(sides) == 2:
            label = 'junction_split_codon'
        else:
            side, model, offset, _ = mapped[0]
            parent = parent_orfs.get(model['transcript_id'])
            start = model.get('annotated_start', parent['start_0based'] if parent else None)
            relative = offset - start if start is not None else -1
            if 'cds_intervals' in model:
                coding_triplet = all(any(lo <= base < hi for lo, hi in model['cds_intervals']) for base in range(offset, offset + 3))
                reference_aa = CODE.get(model['sequence'][offset:offset + 3])
                cds_end = max((hi for lo, hi in model['cds_intervals']), default=0)
            else:  # Small standalone fixture/backward-compatible caller models.
                coding_triplet = bool(parent and 0 <= relative and relative // 3 < len(parent['sequence']))
                reference_aa = parent['sequence'][relative // 3] if coding_triplet else None
                cds_end = parent['start_0based'] + len(parent['sequence']) * 3 if parent else 0
            if start is not None and relative >= 0 and relative % 3 == 0 and coding_triplet and reference_aa == aa:
                label = f'parent_{side}_canonical'
                canonical_index = relative // 3 + 1
            elif start is None:
                label = f'parent_{side}_unannotated_CDS'
            elif relative < 0:
                label = f'parent_{side}_upstream_of_annotated_CDS'
            elif relative % 3:
                label = f'parent_{side}_out_of_frame'
            elif offset >= cds_end:
                label = f'parent_{side}_downstream_of_annotated_CDS'
            else:
                label = f'parent_{side}_noncanonical_amino_acid'
        yield dict(residue_1based=index + 1, amino_acid=aa, source_class=label,
                   nucleotide_sources=';'.join(f'{s}:{m["transcript_id"]}:{o}:{m["chrom"]}:{g}:{m["strand"]}' for s, m, o, g in mapped),
                   canonical_parent_residue_1based=canonical_index)


def adjacent_audit(path, pairs):
    if not path.exists():
        return [], None
    records = json.loads(path.read_text())
    selected = [r for r in records if r['gene_name_5p'] + ':' + r['gene_name_3p'] in pairs]
    return selected, file_sha(path)


def consensus_orf_ids(combos, by_id):
    """No missing/incompatible annotated alternative may silently disappear."""
    relevant = [c for c in combos if c['exclusion_reason'] != 'retained_intron_transcript']
    if not relevant or any(c['exclusion_reason'] or not c['annotated_start_orf_id'] for c in relevant):
        return []
    ids = [c['annotated_start_orf_id'] for c in relevant]
    return ids if len({by_id[i]['sequence_sha256'] for i in ids}) == 1 else []


def run(root=ROOT, output=None):
    root = Path(root)
    out = Path(output) if output else root / 'results/structure_campaign/cohort'
    out.mkdir(parents=True, exist_ok=True)
    data = root / 'results/dataset_reconstruction'
    reference = root / 'results/structure_campaign/cohort/reference_candidates.tsv'
    references = [r for r in read_tsv(reference) if r['primary_reference'] == 'True']
    pairs = {r['pair_id'] for r in references}
    assert len(pairs) == len(references) == 109
    probes = [r for r in read_tsv(data / 'probe_junctions.tsv') if r['pair_id'] in pairs]
    mappings = [r for r in read_tsv(data / 'probe_sequence_mapping.tsv') if r['pair_id'] in pairs]
    gtf = root / 'data/reference/gencode.vM28.annotation.gtf.gz'
    fasta = root / 'data/reference/gencode.vM28.transcripts.fa.gz'
    models = load_transcripts(gtf, fasta, {r['transcript_id'] for r in mappings})
    side_models = defaultdict(list)
    for r in mappings:
        tid = r['transcript_id']
        if tid not in side_models[r['probe_id'], r['side']]:
            side_models[r['probe_id'], r['side']].append(tid)
    parents = {t: orf_at(m['sequence'], m['annotated_start']) for t, m in models.items() if m['annotated_start'] is not None}
    parents = {t: p for t, p in parents.items() if p}
    combinations = []; orfs = []; pair_combos = defaultdict(list)
    for probe in sorted(probes, key=lambda r: r['probe_id']):
        for ta, tb in itertools.product(sorted(side_models[probe['probe_id'], 'a']), sorted(side_models[probe['probe_id'], 'b'])):
            left, right = models[ta], models[tb]
            sequence, junction, b, boundary = reconstruct(left, right, int(probe['breakpoint1']), int(probe['breakpoint2']), probe['sequence'])
            hid = 'transcript_' + sha('|'.join([probe['probe_id'], ta, tb]))
            reason = 'retained_intron_transcript' if any(m['transcript_type'] == 'retained_intron' for m in [left, right]) else 'non_exon_boundary' if not boundary else ''
            record = dict(transcript_hypothesis_id=hid, pair_id=probe['pair_id'], probe_id=probe['probe_id'], transcript_a=ta, transcript_b=tb,
                          donor_breakpoint_1based=int(probe['breakpoint1']), acceptor_breakpoint_1based=int(probe['breakpoint2']),
                          junction_offset_0based=junction, acceptor_offset_0based=b, rna_length_nt=len(sequence), rna_sha256=sha(sequence),
                          sequence_source='reference_annotated_prefix_suffix_not_observed_full_chain', full_chain_observed=False,
                          exact_probe_match=True, annotated_exon_boundaries=boundary, exclusion_reason=reason,
                          annotated_donor_start_0based=left['annotated_start'], annotated_start_orf_id='', retained_exon_chain_a=[], retained_exon_chain_b=[])
            for side, model, low, high in [('a', left, 0, junction), ('b', right, b, len(right['sequence']))]:
                offset = 0
                for exon in model['exons']:
                    size = exon['end'] - exon['start'] + 1
                    lo, hi = max(low, offset), min(high, offset + size)
                    if lo < hi:
                        record[f'retained_exon_chain_{side}'].append(dict(exon_number=exon['exon_number'], transcript_start_0based=lo, transcript_end_0based_exclusive=hi, genomic_first_1based=genomic_base(model, lo), genomic_last_1based=genomic_base(model, hi - 1), chrom=model['chrom'], strand=model['strand']))
                    offset += size
            record['_sequence'] = sequence
            combinations.append(record); pair_combos[probe['pair_id']].append(record)
            if reason:
                continue
            for o in crossing_orfs(sequence, junction):
                peptide_id = 'peptide_' + sha(o['sequence'])
                oid = 'orf_' + sha(f'{hid}|{o["start_0based"]}|{o["stop_start_0based"]}')
                annotated = o['start_0based'] == left['annotated_start']
                x = dict(orf_id=oid, transcript_hypothesis_id=hid, pair_id=probe['pair_id'], probe_id=probe['probe_id'], peptide_id=peptide_id,
                         sequence_sha256=sha(o['sequence']), length_aa=len(o['sequence']), transcript_a=ta, transcript_b=tb,
                         start_0based=o['start_0based'], stop_start_0based=o['stop_start_0based'], junction_offset_0based=junction, acceptor_offset_0based=b,
                         annotated_donor_start=annotated, eligibility_tier='conditional_annotated_start' if annotated else 'alternative_start_sensitivity',
                         strict_primary_eligible=False, full_chain_observed=False, translation_evidence='not_inferred_from_RNA_support',
                         sequence_source='reference_annotated_prefix_suffix', _sequence=o['sequence'])
                orfs.append(x)
                if annotated:
                    record['annotated_start_orf_id'] = oid
    by_id = {r['orf_id']: r for r in orfs}
    consensus_pairs = set()
    for pair, combos in pair_combos.items():
        ids = consensus_orf_ids(combos, by_id)
        if ids:
            consensus_pairs.add(pair)
            for oid in ids:
                by_id[oid]['eligibility_tier'] = 'conditional_consensus'
    peptide_groups = defaultdict(list)
    for o in orfs:
        peptide_groups[o['peptide_id']].append(o)
    peptides = []
    for pid, rows in sorted(peptide_groups.items()):
        tier = min((r['eligibility_tier'] for r in rows), key=TIERS.index)
        peptides.append(dict(peptide_id=pid, sequence_sha256=rows[0]['sequence_sha256'], length_aa=rows[0]['length_aa'], eligibility_tier=tier,
                             strict_primary_eligible=False, conditional_census_eligible=tier in TIERS[:2], pair_ids=';'.join(sorted({r['pair_id'] for r in rows})),
                             orf_ids=';'.join(sorted(r['orf_id'] for r in rows)), sequence=rows[0]['_sequence'], source_confidence='conditional_reference_not_observed_chain',
                             calibration_reference=rows[0]['sequence_sha256'] == 'f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'))
    write_tsv(out / 'peptides.tsv', peptides)
    write_fasta(out / 'peptides.fasta', ((r['peptide_id'], r['sequence']) for r in peptides))
    write_fasta(out / 'primary_peptides.fasta', [])
    write_fasta(out / 'conditional_peptides.fasta', ((r['peptide_id'], r['sequence']) for r in peptides if r['conditional_census_eligible']))
    write_fasta(out / 'consensus_peptides.fasta', ((r['peptide_id'], r['sequence']) for r in peptides if r['eligibility_tier'] == 'conditional_consensus'))
    write_fasta(out / 'sensitivity_peptides.fasta', ((r['peptide_id'], r['sequence']) for r in peptides if r['eligibility_tier'] == TIERS[2]))
    write_fasta(out / 'reference_assisted_transcripts.fasta', ((r['transcript_hypothesis_id'], r['_sequence']) for r in combinations))
    with (out / 'transcript_hypotheses.jsonl').open('w') as f:
        for r in combinations:
            f.write(json.dumps({k: v for k, v in r.items() if not k.startswith('_')}, sort_keys=True) + '\n')
    write_tsv(out / 'orf_hypotheses.tsv', [{k: v for k, v in o.items() if not k.startswith('_')} for o in orfs])
    # Store exact residue mappings for every source hypothesis, not an arbitrary
    # representative map for peptides shared by distinct nucleotide origins.
    fields = ['orf_id', 'peptide_id', 'residue_1based', 'amino_acid', 'source_class', 'nucleotide_sources', 'canonical_parent_residue_1based']
    region_rows = []; control_links = []; control_groups = defaultdict(set)
    with (out / 'residue_map.tsv.gz').open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed, io.TextIOWrapper(compressed, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n'); writer.writeheader()
        for o in orfs:
            origin = dict(start_0based=o['start_0based'], sequence=o['_sequence'])
            residue_rows = list(source_residues(origin, o['junction_offset_0based'], o['acceptor_offset_0based'], models[o['transcript_a']], models[o['transcript_b']], parents))
            for r in residue_rows:
                writer.writerow(dict(orf_id=o['orf_id'], peptide_id=o['peptide_id'], **r))
            for label, group in itertools.groupby(residue_rows, key=lambda r: r['source_class']):
                group = list(group)
                region_rows.append(dict(orf_id=o['orf_id'], peptide_id=o['peptide_id'], source_class=label, start_residue_1based=group[0]['residue_1based'], end_residue_1based=group[-1]['residue_1based']))
                if label not in ['parent_a_canonical', 'parent_b_canonical']:
                    continue
                side = 'a' if label == 'parent_a_canonical' else 'b'
                tid = o['transcript_' + side]
                fragment = ''.join(r['amino_acid'] for r in group)
                ctrl = 'control_' + sha(fragment)
                control_groups[fragment].add('retained_canonical_fragment')
                control_links.append(dict(orf_id=o['orf_id'], peptide_id=o['peptide_id'], control_id=ctrl, control_type='retained_canonical_fragment', transcript_id=tid,
                                          parent_residue_start_1based=group[0]['canonical_parent_residue_1based'], parent_residue_end_1based=group[-1]['canonical_parent_residue_1based'],
                                          candidate_residue_start_1based=group[0]['residue_1based'], candidate_residue_end_1based=group[-1]['residue_1based']))
    # Full parent controls must be explicitly reachable by each originating
    # ORF; transcript-only inventory rows are insufficient for cohort filters.
    for o in orfs:
        for tid in sorted({o['transcript_a'], o['transcript_b']}):
            parent = parents.get(tid)
            if parent:
                control_links.append(dict(orf_id=o['orf_id'], peptide_id=o['peptide_id'], control_id='control_' + sha(parent['sequence']),
                                          control_type='annotated_parent_complete_ORF', transcript_id=tid,
                                          parent_residue_start_1based=1, parent_residue_end_1based=len(parent['sequence']),
                                          candidate_residue_start_1based='', candidate_residue_end_1based=''))
    for tid, parent in sorted(parents.items()):
        control_groups[parent['sequence']].add('annotated_parent_complete_ORF')
        control_links.append(dict(orf_id='', peptide_id='', control_id='control_' + sha(parent['sequence']), control_type='annotated_parent_complete_ORF', transcript_id=tid,
                                  parent_residue_start_1based=1, parent_residue_end_1based=len(parent['sequence']), candidate_residue_start_1based='', candidate_residue_end_1based=''))
    controls = [dict(control_id='control_' + sha(seq), sequence_sha256=sha(seq), length_aa=len(seq), control_types=';'.join(sorted(kinds)), sequence=seq,
                     interpretation='reference_sequence_control_not_experimentally_verified_construct') for seq, kinds in sorted(control_groups.items(), key=lambda x: sha(x[0]))]
    write_tsv(out / 'regions.tsv', region_rows)
    write_tsv(out / 'parent_controls.tsv', controls)
    write_tsv(out / 'control_links.tsv', control_links)
    write_fasta(out / 'parent_controls.fasta', ((r['control_id'], r['sequence']) for r in controls))
    observed_path = Path('/home/ubuntu/workspace/chrna/runs/focused-pilot-20260919/orfs/protein_hypotheses.json')
    adjacent, adjacent_sha = adjacent_audit(observed_path, pairs)
    (out / 'adjacent_read_hypotheses.json').write_text(json.dumps(adjacent, indent=2) + '\n')
    published = [r for r in read_tsv(data / 'junctions.tsv') if r['pair_id'] in pairs]
    write_tsv(out / 'published_junction_evidence.tsv', published)
    pair_rows = []
    for ref in sorted(references, key=lambda r: r['pair_id']):
        pair = ref['pair_id']; oo = [o for o in orfs if o['pair_id'] == pair]; cc = pair_combos[pair]
        conditional = {o['peptide_id'] for o in oo if o['annotated_donor_start']}
        statuses = []
        if any(c['exclusion_reason'] for c in cc):
            statuses.append('excluded_transcript_combinations')
        if not conditional:
            statuses.append('no_complete_crossing_ORF_at_annotated_donor_start')
        elif pair not in consensus_pairs:
            statuses.append('reference_isoform_or_start_ambiguity')
        statuses.append('observed_full_exon_chain_unavailable')
        evidence = [r for r in published if r['pair_id'] == pair]
        pair_rows.append(dict(pair_id=pair, evidence_tier=ref['evidence_tier'], reported_nanostring_support=True, probe_ids=';'.join(sorted({r['probe_id'] for r in cc})),
                              annotated_transcript_combinations=len(cc), excluded_combinations=sum(bool(c['exclusion_reason']) for c in cc), complete_crossing_orf_hypotheses=len(oo),
                              unique_peptide_hypotheses=len({o['peptide_id'] for o in oo}), conditional_annotated_start_peptides=len(conditional), conditional_consensus=pair in consensus_pairs,
                              strict_primary_eligible=False, audit_status=';'.join(statuses), full_chain_status='not_established_from_available_sources',
                              published_junction_records=len(evidence), published_pair_read_ids=';'.join(sorted({v for r in evidence for v in r['read_ids'].split(';')})),
                              read_junction_link_status='pair_only_source_coordinate_convention_unresolved', assay_qc_status=ref['assay_qc_status'], translation_evidence_status='requires_separate_candidate_specific_audit'))
    write_tsv(out / 'pair_audit.tsv', pair_rows)
    counts = dict(primary_reference_pairs=len(pairs), primary_probe_designs=len(probes), annotated_transcript_combinations=len(combinations),
                  excluded_transcript_combinations=sum(bool(c['exclusion_reason']) for c in combinations), strict_primary_peptides=0,
                  conditional_consensus_pairs=len(consensus_pairs), conditional_consensus_unique_peptides=sum(r['eligibility_tier'] == TIERS[0] for r in peptides),
                  conditional_census_pairs=sum(r['conditional_annotated_start_peptides'] > 0 for r in pair_rows), conditional_census_unique_peptides=sum(r['conditional_census_eligible'] for r in peptides),
                  all_complete_crossing_orf_hypotheses=len(orfs), all_unique_peptide_hypotheses=len(peptides), alternative_start_only_unique_peptides=sum(r['eligibility_tier'] == TIERS[2] for r in peptides),
                  unique_parent_control_sequences=len(controls), adjacent_observed_read_hypothesis_overlaps=len(adjacent))
    inputs = [reference, data / 'probe_junctions.tsv', data / 'probe_sequence_mapping.tsv', data / 'junctions.tsv', gtf, fasta,
              root / 'data/raw/41586_2026_10982_MOESM5_ESM.xlsx', root / 'data/raw/41586_2026_10982_MOESM6_ESM.xlsx']
    lengths = sorted(r['length_aa'] for r in peptides if r['conditional_census_eligible'])
    counts['conditional_length_min_aa'] = min(lengths) if lengths else None
    counts['conditional_length_max_aa'] = max(lengths) if lengths else None
    manifest = dict(status='completed_reference_assisted_audit_not_experimental_sequence_resolution', counts=counts, assembly='GRCm39', annotation='GENCODE M28',
                    coordinate_conventions=dict(transcript='0-based half-open', genomic='1-based inclusive', protein='1-based inclusive'),
                    input_sha256={str(p.relative_to(root)): file_sha(p) for p in inputs}, reconstruction_code_sha256=file_sha(Path(__file__)),
                    adjacent_hypothesis_source=str(observed_path), adjacent_hypothesis_source_sha256=adjacent_sha,
                    primary_rule='Observed full-chain and start evidence required; not inferred from pair-level assay support.',
                    conditional_consensus_rule='Same complete >=30-aa crossing peptide from annotated donor start in every compatible non-retained-intron exon-boundary transcript combination; reference hypothesis only.',
                    conditional_census_rule='All complete >=30-aa crossing ORFs from annotated donor starts across eligible reference transcript combinations; no arbitrary isoform or longest-ORF choice.',
                    sensitivity_rule='Every complete forward ATG-to-first-stop >=90 coding-nt crossing ORF; unannotated donor starts remain alternative-start sensitivity.',
                    limitations=['Table3 has read IDs and endpoints but no full exon chains or transcript IDs; Table4 has caller pair lists only.',
                                 'Reference prefix/suffix chains are conditional constructs, not reproduction of author read-specific exon repair.',
                                 'No individual successful assay/QC or translated-protein status is inferred.',
                                 'Read evidence exported at pair level; exact published-to-probe junction matching not asserted.',
                                 'No cloud, structure, disorder or model inference performed by this script.'])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'STATUS.md').write_text('# Structure campaign cohort status\n\nCompleted the 109-pair audit. Strict primary sequence denominator remains zero; conditional reference and alternative-start hypotheses are separate.\n\n```json\n' + json.dumps(counts, indent=2) + '\n```\n')
    (out / 'METHODS.md').write_text("""# Reference-assisted ORF audit

Reproduce with `.venv/bin/python scripts/structure_campaign/reconstruct.py` from the repository root; focused tests are `tests/test_structure_campaign_reconstruct.py`.

The membership source is the 109 NanoString-supported ordered pairs in the frozen 383-pair reference table. All 111 associated probe designs are audited. A pair reporting label does not verify every probe, junction, transcript or ORF. Individual assay/QC and read-to-sample links remain unknown.

**Strict primary is empty:** available sources do not resolve complete observed exon chains and start sites across this cohort. The author spreadsheets contain read IDs/endpoints (Table 3) and caller memberships (Table 4), not the repaired transcript FASTAs or parent isoform IDs. The inspected adjacent pilot overlaps only two unresolved Tyrobp:B2m hypotheses; these are archived and not promoted. The bounded GEO metadata check lists expression XLSX and Salmon quant.sf files, not repaired sequences. Raw-read realignment and transcript resolution were not performed here.

**Conditional hypotheses:** independently enumerate every exact-probe-matched M28 donor/acceptor transcript combination. Retain the annotated donor prefix through its terminal base and acceptor suffix from its first retained base. Check the full reconstruction against all 120 probe nucleotides; never translate the 120-nt probe as a full transcript. Require annotated exon boundaries; exclude retained-intron transcript combinations. All retained exon pieces and reference transcript identifiers are recorded. This assumes the unobserved reference exon chains, transcript termini and alleles; it is not the author's read-specific exon-repair output or proof those transcripts exist.

**ORFs:** enumerate every forward ATG-to-first-in-frame-stop ORF with at least 90 coding nucleotides excluding the stop, with at least one coding nucleotide on each side of the junction. Incomplete and ambiguous-code ORFs are omitted, without classifying their RNAs as noncoding. No longest-ORF selection occurs. Conditional census retains starts annotated in the donor, with complete GTF start-codon support and no cds_start_NF tag. Alternative ATG starts are separate sensitivity hypotheses. A peptide is conditional consensus only when every compatible non-retained-intron reference combination has a crossing annotated-start ORF and every such ORF gives the same peptide. Missing starts, absent crossing ORFs or incompatible boundaries prevent consensus. Consensus is over reference annotations, not proof of an observed isoform. Purely alternative-start peptides are in sensitivity_peptides.fasta; all source hypotheses remain in orf_hypotheses.tsv even when an identical peptide also has stronger evidence.

**Identity and origins:** exact peptide SHA-256 defines peptide IDs and deduplicates computation. Peptide tier is the strongest available source tier; ORF-level tiers and pair mappings preserve other origins. Transcript coordinates are 0-based half-open, genomic bases 1-based inclusive, and amino-acid intervals 1-based inclusive. Every coding nucleotide is mapped to its parent transcript/genomic base; split codons receive both sources. Residue-map rows are per ORF rather than a single arbitrary peptide representative. Parent protein correspondence requires an annotated parent start, actual GTF CDS coverage of the triplet, the same frame and an exact amino-acid match. A partial parent CDS can supply retained-segment mapping even if it lacks a complete parental stop; only complete parent ORFs enter the full-parent control inventory. Out-of-frame, upstream/downstream-CDS and unannotated-CDS sequence classes are separate; a nucleotide parent never supplies an assumed canonical domain to a novel-frame tail.

**Controls:** parent_controls.tsv contains exact annotated-start-to-stop parent ORFs and exact contiguous retained canonical peptide fragments, deduplicated by sequence hash. control_links.tsv identifies each transcript/source ORF and residue interval. Full-parent controls have explicit links to every originating ORF, with candidate residue bounds blank because a complete parent is not an aligned retained fragment; transcript-only inventory rows are also retained. These are sequence controls, not experimental constructs, and the full inventory is not an authorization to fold all controls. Restrict downstream controls to analyzed hypotheses and the campaign cap. No matched-native external control or domain annotation has been fabricated.

**Outputs:** pair_audit.tsv keeps all109 rows and missingness/exclusion reasons. transcript_hypotheses.jsonl plus reference_assisted_transcripts.fasta preserve all1577 combinations, including excluded ones; only eligible combinations yield ORFs. peptides.tsv records strict, conditional and sensitivity inclusion; regions.tsv and residue_map.tsv.gz retain origin maps. published_junction_evidence.tsv retains original read IDs/coordinates at pair level; exact equivalence to probe coordinates is not asserted because Table3 coordinate conventions remain unresolved. Manifest hashes bind inputs, code and outputs. The Gsdmd 118-aa sequence is recognized by its previously verified exact hash as a calibration reference; it was recovered without selecting the expected length or tuning an ORF rule.

These data characterize conditional protein hypotheses linked to an assay-enriched RNA reference. They do not establish protein expression, biological function, experimental disorder, or prevalence among all chRNAs. No cloud, structure or disorder inference is performed by this reconstruction driver.
""")
    manifest['output_sha256'] = {p.name: file_sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in {'manifest.json', 'independent_validation.json'}}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(counts, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.root, args.output)
