"""Coordinate edge cases for the supplementary exon-annotation view."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('exon_annotation', Path(__file__).parents[1]/'scripts/annotate_pilot_exons.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_unquoted_gtf_exon_numbers():
    a = m.attributes('gene_name "Polr2a"; exon_number 14; transcript_id "ENSMUST1";')
    assert a['exon_number'] == '14'
    assert a['gene_name'] == 'Polr2a'


def test_deletions_retained_insertions_excluded_and_minus_reversed():
    a = {'start': 100, 'end': 127, 'cigar': '3S5M2I2D10N4M1I6M', 'strand': '-'}
    assert m.reference_blocks(a) == [(117, 127), (100, 107)]


def test_exon_boundary_is_between_bases():
    tx = {'id': 't1', 'name': 'G-201', 'gene': 'G', 'chromosome': 'chr1', 'strand': '+',
          'exons': [{'start': 100, 'end': 110, 'number': 1, 'id': 'e1', 'source_row': 1}]}
    decision = {'gene_5p': 'g', 'gene_name_5p': 'G', 'biotype_5p': 'protein_coding',
                'boundary_5p': 110,
                'left_alignment': {'start': 100, 'end': 110, 'cigar': '10M', 'strand': '+', 'target': 'chr1'}}
    a = m.arm_data(decision, 0, {'g': {'t1': tx}})
    assert a['adjacent_base_one_based'] == 110
    assert a['choices'][0]['boundary_exons'] == [1]
    assert a['choices'][0]['nearest_edge_delta_nt'] == 0


def test_minus_strand_exon_numbering_and_intronic_extension():
    tx = {'id': 't', 'name': 'G-201', 'gene': 'G', 'chromosome': 'chr1', 'strand': '-',
          'exons': [{'start': 200, 'end': 210, 'number': 1, 'id': 'e1', 'source_row': 1},
                    {'start': 100, 'end': 110, 'number': 2, 'id': 'e2', 'source_row': 2}]}
    result = m.annotate_transcript(tx, [(200, 207), (105, 112)])
    assert [(s['kind'], s['number'], s['rna_start'], s['rna_end']) for s in result['segments']] == [
        ('exon', 1, 0, 7), ('intron', None, 7, 9), ('exon', 2, 9, 14)]
    assert result['nonexonic_nt'] == 2
