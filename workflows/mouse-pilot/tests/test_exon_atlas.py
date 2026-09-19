from chrna.exon_atlas import project_positions, join_positions, codon_frame, choose_transcript, label_position


def test_project_restored_deletions_skips_introns_and_reverses_strand():
    alignment={'start':100,'cigar':'4S3M2I2M2D10N3M1H','strand':'+'}
    assert project_positions(alignment)==[100,101,102,103,104,105,106,117,118,119]
    alignment['strand']='-'
    assert project_positions(alignment)==[119,118,117,106,105,104,103,102,101,100]


def test_overlap_retains_both_loci_without_double_counting_sequence():
    maps=join_positions([1,2,3,4],[8,9,10],-2)
    assert maps==[[('left',1)],[('left',2)],[('left',3),('right',8)],[('left',4),('right',9)],[('right',10)]]
    assert join_positions([1],[8],2)==[[('left',1)],[],[],[('right',8)]]


def test_cds_phase_across_negative_strand_splice():
    # One codon begins in an upstream exon and ends in a downstream exon.
    tx={'strand':'-','cds':[{'start':108,'end':110,'phase':0},{'start':90,'end':94,'phase':1}]}
    maps=[[('left',p)] for p in [109,108,93,92,91,90]]
    assert codon_frame(maps,{'left':tx})==['same annotated CDS frame','same annotated CDS frame']
    assert codon_frame([[('left',p)] for p in [108,93,92]],{'left':tx})==['alternative CDS frame']


def test_transcript_ties_preserved_and_non_exonic_not_called_exon():
    base={'gene_id':'g','strand':'+','gene_type':'protein_coding','exons':[{'start':10,'end':16,'exon_number':2,'exon_id':'e'}],'cds':[],'utr':[{'start':10,'end':16}]}
    txs={k:dict(base,transcript_id=k) for k in ['t2','t1']}
    chosen,candidates,tied=choose_transcript(txs,'g',[11,12],[11,12])
    assert chosen['transcript_id']=='t1' and tied==['t1','t2']
    assert label_position(chosen,12)[1]=='UTR'
    assert label_position(chosen,20)==(None,'non-exonic')


def test_shared_junction_codon_is_not_assigned_a_unique_parental_frame():
    tx={'strand':'+','cds':[{'start':0,'end':9,'phase':0}]}
    maps=[[('left',0)],[('left',1),('right',4)],[('right',5)]]
    assert codon_frame(maps,{'left':tx,'right':tx})==['junction/shared/unmapped codon']
