from chrna.pilot_assessment import parse_alignment, compare_split, decide, GeneIndex, longgf_membership


def alignment(flag,target,pos,cigar,md,mapq=60):
    return parse_alignment(f'r\t{flag}\t{target}\t{pos}\t{mapq}\t{cigar}\t*\t0\t0\t*\t*\tMD:Z:{md}')


def test_reverse_hard_clip_query_coordinates_and_reference_boundaries():
    a=alignment(16,'chr1',101,'100H100M','100')
    assert (a.qstart,a.qend,a.length)==(0,100,200)
    assert (a.start,a.end,a.strand)==(100,200,'-')
    assert a.score(0,100)==100


def test_common_edit_score_charges_indels_and_mismatch_not_splice():
    a=alignment(0,'chr1',1,'4M2D2M','2A1^TT2')
    assert a.score(0,6)==-1
    b=alignment(0,'chr1',1,'3M100N3M','6')
    assert b.score(0,6)==6
    assert b.blocks==[(0,3),(103,106)]


def test_complete_single_transcript_explanation_overrides_split():
    left=alignment(0,'chrA',1,'100M100S','100')
    right=alignment(2048,'chrB',1,'100S100M','100')
    noncoding=alignment(0,'retained_intron_or_lncRNA',1,'200M','200')
    comparison=compare_split(left,right,[noncoding],[left,right])
    ga={'gene_id':'A','exonic_overlap':100};gb={'gene_id':'B','exonic_overlap':100}
    assert comparison['split_single_margin']==0
    assert decide(left,right,[ga],[gb],ga,gb,comparison)[0]=='single_transcript_explained'


def test_supported_singleton_and_alternative_mapping_ambiguity():
    left=alignment(0,'chrA',1,'100M100S','100')
    right=alignment(2048,'chrB',1,'100S100M','100')
    partial=alignment(0,'parentA',1,'100M100S','100')
    ga={'gene_id':'A','exonic_overlap':100};gb={'gene_id':'B','exonic_overlap':100}
    comparison=compare_split(left,right,[partial],[left,right])
    assert decide(left,right,[ga],[gb],ga,gb,comparison)[0]=='supported_two_gene_junction'
    alt=alignment(256,'chrC',1,'100M100S','100')
    comparison=compare_split(left,right,[partial],[left,right,alt])
    assert decide(left,right,[ga],[gb],ga,gb,comparison)[0]=='ambiguous_single_vs_split'


def test_exon_union_does_not_double_count_isoforms(tmp_path):
    p=tmp_path/'test.gtf'
    p.write_text('chrA\ttest\texon\t1\t100\t.\t+\t.\tgene_id "A"; gene_name "A"; gene_type "lncRNA";\n'*2)
    index=GeneIndex(p)
    assert index.assign(alignment(0,'chrA',1,'100M','100'))==[{'gene_id':'A','exonic_overlap':100}]
    assert index.genes['A']['biotype']=='lncRNA'


def test_longgf_read_identifiers_preserve_slashes(tmp_path):
    p=tmp_path/'LongGF.log'
    p.write_text('GF\tA:B 1\n\t1400(+chrA:1100-1400/SRR123.55/1:0-300)1 2199(+chrB:2199-2499/299-599)1\nSumGF\tA:B\n')
    assert dict(longgf_membership(p))=={'SRR123.55/1':{'A:B'}}
