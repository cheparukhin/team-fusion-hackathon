import math
import numpy as np
import pytest
from chrna.hic import coordinate_bin,genova_enrichment,extract_window,aggregate_bin_pair_features

def test_one_based_boundary():
    assert coordinate_bin(500000)==0
    assert coordinate_bin(500001)==1
    with pytest.raises(ValueError):coordinate_bin(0)

def test_genova_quadrants_and_missing_background():
    a=np.ones((11,11))*2
    a[4:7,:]=100
    a[:,4:7]=100
    a[4:7,4:7]=8
    assert genova_enrichment(a)==(8.,2.,4.,'observed')
    a[:4,:4]=0;a[:4,7:]=0;a[7:,:4]=0;a[7:,7:]=0
    assert math.isnan(genova_enrichment(a)[2])
    a[0,0]=np.nan
    assert genova_enrichment(a)[3]=='unavailable_pixels'

def test_edges_and_reversed_order():
    a=np.arange(400).reshape(20,20)
    assert extract_window(a,4,10) is None
    assert np.array_equal(extract_window(a,10,8).T,extract_window(a.T,8,10))

def test_aggregate_deduplicates_bins_and_requires_all_replicates():
    rows=[dict(pair_id='A:B',replicate=r,chrom1='chr1',bin1=10,chrom2='chr2',bin2=20,enrichment=v,status='observed') for r,v in [('A',1.),('A',1.),('B',2.),('C',3.)]]
    x=aggregate_bin_pair_features(rows,['A:B','B:A'])
    assert x[0]['hic_contact_enrichment']==2
    assert x[0]['hic_n_bin_pairs']==1
    assert math.isnan(x[1]['hic_feature'])
    assert math.isnan(aggregate_bin_pair_features(rows[:3],['A:B'])[0]['hic_feature'])

def test_star_matching_preserves_order_strands_and_both_breakpoints():
    import importlib.util,pathlib,pandas as pd
    spec=importlib.util.spec_from_file_location('match_junctions',pathlib.Path(__file__).parents[1]/'scripts/compute/match_junctions.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    assert mod.terminal_coordinates(101,'+',199,'+')==(100,200)
    assert mod.terminal_coordinates(99,'-',201,'-')==(100,200)
    probes=pd.DataFrame([dict(pair_id='A:B',probe_id='p',chrom1='chr1',strand1='+',breakpoint1=100,chrom2='chr2',strand2='+',breakpoint2=200)])
    lines=['chr1\t111\t+\tchr2\t209\t+\t0\t0\t0\tread1','chr1\t111\t+\tchr2\t210\t+\t0\t0\t0\tread2','chr2\t201\t+\tchr1\t99\t+\t0\t0\t0\tread3']
    lines.append('chr1\t101\t+\tchr2\t199\t+\t-1\t0\t0\tmate_only')
    out=mod.match(probes,lines)
    assert [r['read_id'] for r in out]==['read1']
    reverse=mod.match(probes,['chr2\t199\t-\tchr1\t101\t-\t2\t0\t0\tantisense'])
    assert len(reverse)==1 and reverse[0]['pair_id']=='A:B'
    assert reverse[0]['match_orientation']=='reverse_complement'
    assert (reverse[0]['chrom1'],reverse[0]['terminal1'],reverse[0]['strand1'])==('chr1',100,'+')
    assert reverse[0]['raw_star_chrom1']=='chr2'


def test_missing_kr_bins_are_not_observed_zero_contacts():
    from chrna.hic import mask_invalid_normalization
    a=np.zeros((11,11));a[4:7,4:7]=5
    a[0,0]=2
    norm=np.ones(11);norm[0]=np.nan
    masked=mask_invalid_normalization(a,norm,np.ones(11))
    assert np.isnan(masked[0,:]).all()
    assert masked[1,1]==0
    assert genova_enrichment(masked)[3]=='unavailable_pixels'
    assert np.isnan(mask_invalid_normalization(a,np.array([]),np.ones(11))).all()
