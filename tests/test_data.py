from pathlib import Path
import pandas as pd
from chrna.data import aggregate_reads, gene_identity, genomic_context, resolve_probe, transcript_coordinate


def test_read_union_retains_order_and_ignores_caller_duplicates():
    rows=pd.DataFrame({'pair_id':['A:B','A:B','A:B','B:A'],'read_id':['read1','read1','read2','read1']})
    assert aggregate_reads(rows).to_dict()=={'A:B':2,'B:A':1}


def test_transcript_mapping_crosses_exons_and_respects_reverse_strand():
    plus=[(100,109,'chr1','+'),(200,209,'chr1','+')]
    minus=[(100,109,'chr1','-'),(200,209,'chr1','-')]
    assert transcript_coordinate(plus,10)==('chr1',200,'+')
    assert transcript_coordinate(minus,0)==('chr1',209,'-')
    assert transcript_coordinate(minus,10)==('chr1',109,'-')


def test_suffix_requires_two_parent_sequence_matches():
    genes={'A':[{}],'B':[{}]};tx={'A':[('ta','ga','A'*60)],'B':[('tb','gb','C'*60)]}
    ex={'ta':[(1,60,'chr1','+')],'tb':[(101,160,'chr2','-')]}
    pair,a,b,status=resolve_probe('A:B_2','A'*60+'C'*60,genes,tx,ex)
    assert pair=='A:B' and status=='sequence_verified_design_suffix'
    assert resolve_probe('A:B_2','G'*60+'C'*60,genes,tx,ex)[0] is None


def test_minimum_gene_interval_distance_and_unavailable_mapping():
    a=[{'chrom':'chr1','start':100,'end':200},{'chrom':'chr1','start':300,'end':400}]
    assert genomic_context(a,[{'chrom':'chr1','start':450,'end':500}])==(0,50)
    assert genomic_context(a,[{'chrom':'chr1','start':150,'end':160}])==(0,0)
    assert genomic_context(a,[{'chrom':'chr2','start':150,'end':160}])==(1,0)
    assert genomic_context([],a)==(None,None)


def test_multiple_gene_records_require_same_mgi_and_locus_context():
    a={'mgi_id':'MGI:1','chrom':'chr1','strand':'+'}
    assert gene_identity([a,a])=='multiple_gencode_records_same_mgi'
    assert gene_identity([a,{**a,'mgi_id':'MGI:2'}])=='ambiguous_gene_identity'


def test_cached_reconstruction_integrity():
    root=Path(__file__).resolve().parents[1]/'results/dataset_reconstruction'
    panel=pd.read_csv(root/'probe_panel.tsv',sep='\t')
    model=pd.read_csv(root/'model_input.tsv',sep='\t')
    reads=pd.read_csv(root/'read_evidence.tsv',sep='\t')
    assert len(panel)==529 and panel.probe_id.nunique()==529
    assert len(model)==479 and int(model.label.sum())==109
    assert panel.drop_duplicates("pair_id").reported_nanostring_support.sum()==109
    assert panel.reported_nanostring_support.sum()==111
    assert set(panel.label_scope)=={"ordered_gene_pair_not_probe_or_junction"}
    assert reads.read_id.nunique()==36826 and reads.pair_id.nunique()==30390
    assert model.sample_count.isna().all()
    assert set(model.assay_tested)=={'unknown'} and set(model.assay_qc_status)=={'unknown'}
    excluded=panel[panel.exclusion_reason.notna()]
    assert len(excluded)==48 and excluded.label.sum()==0
    assert set(model.pair_id)==set(panel[panel.exclusion_reason.isna()].pair_id)
    assert model.long_read_support.to_dict()==model.pair_id.map(aggregate_reads(reads)).to_dict()
    assert set(['Aoah:Sirt5','Tbc1d23:Xdh','Gsdmd:Tmem106a','Cd274:Lacc1']) <= set(model.pair_id)
    assert all(model.parent_a+':'+model.parent_b==model.pair_id)
