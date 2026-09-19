import pytest

from chrna.reference_audit import audit, fasta_lengths


def fixture(tmp_path):
    genome = tmp_path / "genome.fa"
    genome.write_text(">chr1\nACGTACGTACGT\n")
    transcriptome = tmp_path / "transcripts.fa"
    transcriptome.write_text(">t1.1|g1.1|metadata\nACGT\n>t2.1|g2.1|metadata\nACGTAC\n")
    gtf = tmp_path / "annotation.gtf"
    lines = []
    for tid, biotype, end in [("t1.1", "protein_coding", 4), ("t2.1", "lncRNA", 6)]:
        for feature in ["transcript", "exon"]:
            lines.append(f'chr1\tfixture\t{feature}\t1\t{end}\t.\t+\t.\ttranscript_id "{tid}"; transcript_type "{biotype}";')
    gtf.write_text("\n".join(lines) + "\n")
    return genome, gtf, transcriptome


def test_comprehensive_reference_retains_noncoding(tmp_path):
    result = audit(*fixture(tmp_path))
    assert result["compatible_for_alignment"]
    assert result["transcript_biotypes"] == {"lncRNA": 1, "protein_coding": 1}


def test_absent_contig_and_coordinate_bounds(tmp_path):
    genome, gtf, transcriptome = fixture(tmp_path)
    gtf.write_text(gtf.read_text().replace("chr1", "chrMissing", 1).replace("\t6\t", "\t99\t"))
    result = audit(genome, gtf, transcriptome)
    assert not result["compatible_for_alignment"]
    assert result["annotation_contigs_absent_from_genome"] == {"chrMissing": 1}
    assert result["invalid_gtf_coordinate_rows"]
    assert result["exon_length_discrepancies"]


def test_missing_noncoding_transcript_blocks_compatibility(tmp_path):
    genome, gtf, transcriptome = fixture(tmp_path)
    transcriptome.write_text(">t1.1\nACGT\n")
    result = audit(genome, gtf, transcriptome)
    assert not result["compatible_for_alignment"]
    assert result["annotation_transcripts_missing_from_fasta"] == ["t2.1"]


def test_duplicate_fasta_identifier_rejected(tmp_path):
    path = tmp_path / "bad.fa"
    path.write_text(">t1|a\nACGT\n>t1|b\nACGT\n")
    with pytest.raises(ValueError, match="Duplicate"):
        fasta_lengths(path, gencode=True)
