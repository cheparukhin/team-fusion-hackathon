from chrna.pilot_orfs import CODONS, IndexedFasta, overlap_indels, project_arm, revcomp, spanning_orfs


def test_continuous_translation_across_non_parental_frame_boundary():
    rna='ATG'+'GCT'*40+'TAA'
    records=spanning_orfs(rna,35,35)
    assert len(records)==1
    assert records[0]['protein']=='M'+'A'*40
    assert records[0]['coding_nt']==123
    assert records[0]['frame']==0
    assert len(CODONS)==64
    assert CODONS['TGA']=='*' and CODONS['TGG']=='W'


def test_nonspanning_partial_and_ambiguous_orfs_are_not_eligible():
    assert not spanning_orfs('ATG'+'GCT'*40,35,35)  # no observed stop
    assert not spanning_orfs('ATG'+'GCT'*40+'TAA',2,2)  # no upstream support
    assert not spanning_orfs('ATG'+'GCT'*10+'NNN'+'GCT'*30+'TAA',35,35)


def fasta(tmp_path):
    p=tmp_path/'ref.fa'
    p.write_text('>chr1\nATGAAACCC\n')
    (tmp_path/'ref.fa.fai').write_text('chr1\t9\t6\t9\t10\n')
    return IndexedFasta(p)


def test_reference_assistance_preserves_high_quality_variant(tmp_path):
    genome=fasta(tmp_path)
    assert genome.fetch('chr1',2,7)=='GAAAC'
    a={'strand':'+','start':0,'target':'chr1','cigar':'9M'}
    seq,changes,unresolved=project_arm(a,genome,'ATGAAATCC','I'*9)
    assert seq=='ATGAAATCC' and not unresolved
    assert changes[0]['action']=='retain_high_quality_observed_substitution'
    seq,changes,unresolved=project_arm(a,genome,'ATGAAATCC','!'*9)
    assert seq=='ATGAAACCC' and not unresolved
    assert changes[0]['action']=='reference_assisted_low_quality_correction'


def test_high_quality_indel_remains_unresolved(tmp_path):
    genome=fasta(tmp_path)
    a={'strand':'+','start':0,'target':'chr1','cigar':'3M1I6M'}
    seq,changes,unresolved=project_arm(a,genome,'ATGCAAACCC','I'*10)
    assert seq=='ATGAAACCC'
    assert unresolved[0]['reason']=='high_quality_insertion'


def test_reverse_projection_follows_rna_orientation(tmp_path):
    genome=fasta(tmp_path)
    seq=revcomp('ATGAAACCC')
    a={'strand':'-','start':0,'target':'chr1','cigar':'9M'}
    projected,changes,unresolved=project_arm(a,genome,seq,'I'*9)
    assert projected==seq and not changes and not unresolved


def test_overlap_indel_detection_uses_original_read_coordinates():
    a={'strand':'+','cigar':'3M1I6M'}
    assert overlap_indels(a,(2,5),10)[0]['original_query_interval']==[3,4]
    assert not overlap_indels(a,(7,10),10)
    a['strand']='-'
    assert overlap_indels(a,(6,8),10)[0]['original_query_interval']==[6,7]
    assert not overlap_indels(a,(2,5),10)
    assert overlap_indels({'strand':'-','cigar':'3M2D7M'},(6,8),10)[0]['original_query_interval']==[7,7]
