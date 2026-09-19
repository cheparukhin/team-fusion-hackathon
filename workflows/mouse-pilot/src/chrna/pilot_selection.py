"""RNA-only protein shortlist; explicit freeze precedes folding and outcome joins."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def near_identical(a, b):
    """Global unit-cost edit distance <=5% of the longer amino-acid sequence."""
    limit = max(len(a), len(b)) // 20
    if abs(len(a) - len(b)) > limit:
        return False
    previous = {j: j for j in range(min(len(b), limit) + 1)}
    for i, aa in enumerate(a, 1):
        current = {}
        for j in range(max(0, i - limit), min(len(b), i + limit) + 1):
            current[j] = min(previous.get(j, limit + 1) + 1,
                             current.get(j - 1, limit + 1) + 1,
                             previous.get(j - 1, limit + 1) + (aa != b[j - 1]) if j else i)
        previous = current
    return previous.get(len(b), limit + 1) <= limit


def select(ranking, reconstructions, hypotheses):
    by_junction = defaultdict(list)
    by_reconstruction = defaultdict(list)
    for h in hypotheses:
        if h['longest_spanning_orf_for_read']:
            by_junction[h['junction_id']].append(h)
    for r in reconstructions:
        by_reconstruction[r['junction_id']].append(r)
    ledger, eligible = [], []
    for r in sorted(ranking, key=lambda x: x['display_rank']):
        jid = r['junction_id']
        recs = by_reconstruction[jid]
        primary = by_junction[jid]
        row = {'junction_id': jid, 'rna_rank': r['display_rank'],
               'rna_evidence_state': r['evidence_state'],
               'rna_rank_min': r['rank_min'], 'rna_rank_max': r['rank_max'],
               'distinct_qualifying_reads': r['distinct_qualifying_reads'],
               'status': 'deferred', 'reasons': [],
               'primary_sequence_ids': sorted({h['protein_id'] for h in primary})}
        ledger.append(row)
        if r['evidence_state'] != 'supported_two_gene_junction':
            row['reasons'].append('RNA_evidence_not_supported')
            continue
        if not recs:
            row['reasons'].append('outside_reconstruction_batch_or_missing_read')
            continue
        if len({x['read_id'] for x in recs}) != r['distinct_qualifying_reads']:
            row['reasons'].append('supporting_read_reconstruction_incomplete')
        if any(x['unresolved_sequence_reasons'] for x in recs):
            row['reasons'].append('unresolved_sequence_in_supporting_reads')
        if not primary:
            row['reasons'].append('no_complete_junction_spanning_ORF')
        elif len({h['sequence'] for h in primary}) != 1:
            row['reasons'].append('conflicting_primary_protein_sequences_across_reads')
        if any(not h['sequence_resolved_under_assumptions'] for h in primary):
            row['reasons'].append('primary_sequence_unresolved')
        if row['reasons']:
            continue
        h = sorted(primary, key=lambda x: x['read_id'])[0]
        digest = hashlib.sha256(h['sequence'].encode()).hexdigest()
        if digest != h['sequence_sha256'] or h['protein_id'] != 'protein_' + digest:
            raise ValueError('Protein sequence identity does not match its digest')
        if not h['sequence'] or set(h['sequence']) - set('ACDEFGHIKLMNPQRSTVWY'):
            raise ValueError('Unresolved or invalid amino acids in eligible sequence')
        rec = next(x for x in recs if x['read_id'] == h['read_id'])
        bounds = rec['reference_assisted_junction_interval']
        phases = tuple((b - h['orf']['start']) % 3 for b in bounds)
        junction_class = ('interchromosomal' if r['chromosome_5p'] != r['chromosome_3p'] else 'intrachromosomal',
                          r['strand_5p'] + r['strand_3p'], *phases)
        row.update(status='eligible', protein_id=h['protein_id'],
                   junction_class=list(junction_class),
                   protein_supporting_read_ids=sorted({p['read_id'] for p in primary}),
                   supporting_reads_without_complete_ORF=sorted({x['read_id'] for x in recs} - {p['read_id'] for p in primary}))
        eligible.append((row, h))

    selected = []

    def add(candidate, reason):
        row, h = candidate
        redundant = next((p for p in selected if near_identical(h['sequence'], p['sequence'])), None)
        if redundant:
            row.update(status='deferred', reasons=['redundant_amino_acid_sequence'],
                       representative_protein_id=redundant['protein_id'])
            return False
        row.update(status='selected', reasons=[reason])
        selected.append({**h, 'selection_reason': reason, 'selection_order': len(selected) + 1,
                         'junction_class': row['junction_class'],
                         'protein_supporting_read_ids': row['protein_supporting_read_ids'],
                         'rna_rank_min': row['rna_rank_min'], 'rna_rank_max': row['rna_rank_max']})
        return True

    for candidate in eligible:
        if len(selected) == 8:
            break
        add(candidate, 'top_ranked_distinct_protein')
    for criterion, reason in (
        (lambda row: row['distinct_qualifying_reads'] == 1, 'diversity_supported_singleton'),
        (lambda row: row['junction_class'] not in [p['junction_class'] for p in selected], 'diversity_junction_class'),
    ):
        if len(selected) >= 10:
            break
        for candidate in eligible:
            if candidate[0]['status'] == 'eligible' and criterion(candidate[0]) and add(candidate, reason):
                break
    for candidate in eligible:
        row, h = candidate
        if row['status'] != 'eligible':
            continue
        if len(selected) < 10:
            add(candidate, 'ranked_fill_unavailable_diversity_slot')
        else:
            row.update(status='deferred', reasons=['folding_batch_limit'])
    for row in ledger:
        if row['status']=='selected':
            category='selected_for_folding'
        elif row['rna_evidence_state']=='single_transcript_explained':
            category='technically_excluded_single_transcript_explanation'
        elif row['rna_evidence_state']!='supported_two_gene_junction':
            category='unresolved_RNA_evidence'
        elif 'outside_reconstruction_batch_or_missing_read' in row['reasons']:
            category='deferred_reconstruction_batch'
        elif 'folding_batch_limit' in row['reasons']:
            category='deferred_folding_batch'
        elif 'redundant_amino_acid_sequence' in row['reasons']:
            category='deferred_redundant_sequence'
        else:
            category='unresolved_protein_sequence_or_complete_ORF'
        row['disposition_category']=category
    return {'selected': selected, 'decisions': ledger,
            'limitations': ['Reference-assisted sequence hypotheses; protein existence and function UNKNOWN.',
                            'Read support from one sample is not biological replication.',
                            'Junction class uses chromosome, strand and reconstructed ORF boundary phase, not parental CDS frame.',
                            'RNA ties retain their rank interval; stable junction ID breaks display/selection ties.',
                            'Unreconstructed junctions are deferred, not absent proteins.']}


def run(assessment, orfs, rules, output, freeze=False):
    inputs = {'ranking': assessment / 'rna_ranking.json',
              'decisions': assessment / 'read_decisions.json',
              'read_identity': assessment.parent / 'read_identity.tsv',
              'reconstructions': orfs / 'reconstructions.json',
              'hypotheses': orfs / 'protein_hypotheses.json', 'rules': rules,
              'selection_code': Path(__file__)}
    content = {k: p.read_bytes() for k, p in inputs.items()}
    result = select(*(json.loads(content[k]) for k in ('ranking', 'reconstructions', 'hypotheses')))
    receipt = {'status': 'frozen' if freeze else 'preview_not_frozen',
               'created_utc': datetime.now(timezone.utc).isoformat(),
               'inputs': {k: {'path': str(inputs[k].resolve()), 'sha256': hashlib.sha256(v).hexdigest()}
                          for k, v in content.items()},
               'selected_proteins': len(result['selected']),
               'published_outcomes_used': False, 'learned_scorer_used': False}
    # A new directory prevents accidental replacement of a frozen selection.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'rna_ranking.json').write_bytes(content['ranking'])
    (output / 'read_decisions.json').write_bytes(content['decisions'])
    (output / 'read_identity.tsv').write_bytes(content['read_identity'])
    (output / 'selection_rules.md').write_bytes(content['rules'])
    (output / 'selection.json').write_text(json.dumps(result, indent=2) + '\n')
    (output / 'selected_proteins.fasta').write_text(''.join(
        f'>{h["protein_id"]} junction={h["junction_id"]} source=reference_assisted\n{h["sequence"]}\n'
        for h in result['selected']))
    receipt['outputs'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    (output / 'freeze.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assessment', type=Path, required=True)
    parser.add_argument('--orfs', type=Path, required=True)
    parser.add_argument('--rules', type=Path, default=Path('docs/focused_pilot_rules.md'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.assessment, args.orfs, args.rules, args.output, args.freeze), indent=2))


if __name__ == '__main__':
    main()
