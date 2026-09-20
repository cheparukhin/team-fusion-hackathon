"""Boundary and provenance checks for reference-assisted ORF reconstruction."""
import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('campaign_reconstruct', Path(__file__).parents[1] / 'scripts/structure_campaign/reconstruct.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def model(strand='+'):
    exons = [{'start': 10, 'end': 12, 'exon_number': 1}, {'start': 30, 'end': 35, 'exon_number': 2}]
    if strand == '-':
        exons = [dict(exons[1], exon_number=1), dict(exons[0], exon_number=2)]
    return dict(transcript_id='tx', chrom='chr1', strand=strand, exons=exons)


@pytest.mark.parametrize('strand,positions', [('+', [10, 11, 12, 30, 31, 32, 33, 34, 35]), ('-', [35, 34, 33, 32, 31, 30, 12, 11, 10])])
def test_strand_and_splice_coordinate_round_trip(strand, positions):
    transcript = model(strand)
    for offset, base in enumerate(positions):
        assert m.genomic_base(transcript, offset) == base
        assert m.tx_offset(transcript, base) == offset
    with pytest.raises(ValueError):
        m.tx_offset(transcript, 20)
    with pytest.raises(ValueError):
        m.genomic_base(transcript, len(positions))


def test_complete_crossing_orfs_keep_alternative_starts():
    rna = 'ATGATGAAATAA'
    candidates = m.crossing_orfs(rna, 7, min_coding_nt=6)
    assert [(r['start_0based'], r['stop_start_0based'], r['sequence']) for r in candidates] == [(0, 9, 'MMK'), (3, 9, 'MK')]
    # A stop codon on the other parent is insufficient when no coding base crosses.
    assert m.crossing_orfs(rna, 9, min_coding_nt=6) == []
    assert m.crossing_orfs('ATGAAACCC', 4, min_coding_nt=6) == []
    assert m.crossing_orfs('ATGNNNTAA', 4, min_coding_nt=6) == []


def test_exact_probe_verification_not_probe_translation():
    left = dict(transcript_id='a', chrom='chr1', strand='+', exons=[dict(start=1, end=80, exon_number=1), dict(start=101, end=140, exon_number=2)], sequence='A' * 120)
    right = dict(transcript_id='b', chrom='chr2', strand='-', exons=[dict(start=201, end=220, exon_number=1), dict(start=81, end=180, exon_number=2)], sequence='C' * 120)
    rna, junction, offset, boundaries = m.reconstruct(left, right, 80, 180, 'A' * 60 + 'C' * 60)
    assert rna == 'A' * 80 + 'C' * 100
    assert (junction, offset, boundaries) == (80, 20, True)
    with pytest.raises(ValueError, match='probe'):
        m.reconstruct(left, right, 80, 180, 'G' * 120)


def test_split_codon_origin_does_not_invent_parent_domain():
    left = dict(transcript_id='a', chrom='chr1', strand='+', exons=[dict(start=101, end=112, exon_number=1)])
    right = dict(transcript_id='b', chrom='chr2', strand='-', exons=[dict(start=201, end=230, exon_number=1)])
    parent = {'a': dict(start_0based=0, sequence='MK'), 'b': dict(start_0based=0, sequence='MMMMMMMMMM')}
    rows = list(m.source_residues(dict(start_0based=0, sequence='MKP'), 4, 10, left, right, parent))
    assert rows[0]['source_class'] == 'parent_a_canonical'
    assert rows[0]['canonical_parent_residue_1based'] == 1
    assert rows[1]['source_class'] == 'junction_split_codon'
    assert rows[1]['nucleotide_sources'] == 'a:a:3:chr1:104:+;b:b:10:chr2:220:-;b:b:11:chr2:219:-'
    assert rows[1]['canonical_parent_residue_1based'] == ''
    assert rows[2]['source_class'] == 'parent_b_noncanonical_amino_acid'
    assert rows[2]['canonical_parent_residue_1based'] == ''


def test_first_in_frame_stop_wins():
    assert m.orf_at('ATGAAATAAATGCCCTAA', 0)['sequence'] == 'MK'
    assert m.orf_at('CTGAAATAA', 0) is None


def test_consensus_rejects_missing_orf_and_discordant_isoforms():
    combos = [dict(exclusion_reason='', annotated_start_orf_id='a'), dict(exclusion_reason='', annotated_start_orf_id='b')]
    same = {'a': {'sequence_sha256': 'same'}, 'b': {'sequence_sha256': 'same'}}
    assert m.consensus_orf_ids(combos, same) == ['a', 'b']
    assert m.consensus_orf_ids(combos, dict(same, b={'sequence_sha256': 'different'})) == []
    assert m.consensus_orf_ids(combos + [dict(exclusion_reason='', annotated_start_orf_id='')], same) == []
    assert m.consensus_orf_ids(combos + [dict(exclusion_reason='non_exon_boundary', annotated_start_orf_id='')], same) == []
    assert m.consensus_orf_ids(combos + [dict(exclusion_reason='retained_intron_transcript', annotated_start_orf_id='')], same) == ['a', 'b']


def test_partial_parent_cds_can_map_retained_region_without_complete_parent_orf():
    left = dict(transcript_id='partial', chrom='chr1', strand='+', exons=[dict(start=101, end=109, exon_number=1)], annotated_start=0, cds_intervals=[(0, 9)], sequence='ATGAAACCC')
    right = dict(transcript_id='right', chrom='chr2', strand='+', exons=[dict(start=201, end=209, exon_number=1)])
    # No full parental ATG-to-stop ORF exists, but its retained CDS is annotated.
    rows = list(m.source_residues(dict(start_0based=0, sequence='MK'), 7, 0, left, right, {}))
    assert [r['source_class'] for r in rows] == ['parent_a_canonical', 'parent_a_canonical']
    assert [r['canonical_parent_residue_1based'] for r in rows] == [1, 2]
