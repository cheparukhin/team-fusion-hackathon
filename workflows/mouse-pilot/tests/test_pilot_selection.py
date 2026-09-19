import hashlib
import random

from chrna.pilot_selection import near_identical, select


def case(i, sequence, reads=1):
    jid = f'junction_{i}'
    digest = hashlib.sha256(sequence.encode()).hexdigest()
    rank = dict(junction_id=jid, display_rank=i, rank_min=i, rank_max=i,
                distinct_qualifying_reads=reads, evidence_state='supported_two_gene_junction',
                chromosome_5p='chr1', chromosome_3p='chr2', strand_5p='+', strand_3p='+')
    recs = [dict(junction_id=jid, read_id=f'r{i}_{j}', unresolved_sequence_reasons=[],
                 reference_assisted_junction_interval=[60, 60]) for j in range(reads)]
    hs = [dict(junction_id=jid, read_id=r['read_id'], sequence=sequence,
               protein_id='protein_' + digest, sequence_sha256=digest,
               longest_spanning_orf_for_read=True, sequence_resolved_under_assumptions=True,
               orf={'start': 0}, rna_rank=i) for r in recs]
    return rank, recs, hs


def test_conflicting_read_sequences_defer_junction_without_changing_rna_rank():
    rank, recs, hs = case(1, 'M' + 'A'*39, reads=2)
    hs[1]['sequence'] = 'M' + 'G'*39
    result = select([rank], recs, hs)
    assert result['selected'] == []
    assert 'conflicting_primary_protein_sequences_across_reads' in result['decisions'][0]['reasons']
    assert rank['evidence_state'] == 'supported_two_gene_junction'


def test_unresolved_or_missing_supporting_read_cannot_be_silently_ignored():
    rank, recs, hs = case(1, 'M' + 'A'*39, reads=2)
    recs[1]['unresolved_sequence_reasons'] = [{'reason': 'high_quality_insertion'}]
    assert not select([rank], recs, hs)['selected']
    assert not select([rank], recs[:1], hs[:1])['selected']


def test_near_identical_global_distance_handles_indels_and_length():
    assert near_identical('M' + 'A'*39, 'M' + 'A'*38 + 'G')
    assert near_identical('M' + 'A'*39, 'M' + 'A'*41)
    assert not near_identical('M' + 'A'*39, 'M' + 'A'*42)
    assert not near_identical('M' + 'A'*39, 'M' + 'G'*39)


def test_diversity_slot_and_redundancy_preserve_rna_order():
    rng = random.Random(13)
    sequences = ['M' + ''.join(rng.choices('ACDEFGHIKLMNPQRSTVWY', k=59)) for _ in range(13)]
    cases = [case(i + 1, seq, reads=1 if i == 11 else 2) for i, seq in enumerate(sequences)]
    cases[12][0]['chromosome_3p'] = 'chr1'
    result = select([x[0] for x in cases], [r for x in cases for r in x[1]], [h for x in cases for h in x[2]])
    assert [h['rna_rank'] for h in result['selected']] == list(range(1, 9)) + [12, 13]
    assert result['selected'][8]['selection_reason'] == 'diversity_supported_singleton'
    assert result['selected'][9]['selection_reason'] == 'diversity_junction_class'
    a, b = case(1, sequences[0]), case(2, sequences[0][:-1] + 'A')
    result = select([a[0], b[0]], a[1] + b[1], a[2] + b[2])
    assert len(result['selected']) == 1
    assert result['decisions'][1]['reasons'] == ['redundant_amino_acid_sequence']
