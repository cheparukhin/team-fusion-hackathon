from pathlib import Path
from chrna.k562 import star_key,expected_top,compare,illumina_evidence
from chrna.pilot_assessment import assess

def test_star_coordinates_and_antisense_order():
    assert star_key('chr22 101 + chr9 200 + 1 0 0'.split())==('chr22',100,'+','chr9',200,'+')
    assert star_key('chr22 100 - chr9 201 - 1 0 0'.split())==('chr22',100,'-','chr9',200,'-')
    assert star_key('chr9 200 - chr22 101 - 2 0 0'.split())==('chr22',100,'+','chr9',200,'+')
    assert star_key('chr22 101 + chr9 200 + -1 0 0'.split()) is None
    assert star_key('chr22 101 + chr9 200 + 0 0 0'.split()) is None

def test_fractional_ties_and_empty_denominators():
    rows=[{'junction_id':str(i),'rank_min':1,'rank_max':3,'distinct_qualifying_reads':1} for i in range(3)]
    assert expected_top(rows,{'0'},2)['expected_supported']==2/3
    assert expected_top(rows,{'0'},2,True)['expected_supported']==2/3
    assert compare([],[])['a_to_b'] is None

def test_illumina_only_resolved_split_and_unique_fragment(tmp_path):
    p=tmp_path/'star.tsv';f='chr22 101 + chr9 200 + 1 0 0 r1 50 50M50S 201 50S50M 1 100 50 100 100 0\n'
    p.write_text(f+f+f.replace('1 0 0 r1','-1 0 0 r2')+f.replace('1 0 0 r1','1 1 0 r3'))
    evidence,geometry,stats=illumina_evidence(p)
    assert evidence[('chr22',100,'+','chr9',200,'+')]=={'r1'}
    assert stats['repeat_ambiguous']==1 and stats['discordant_or_unoriented']==1

def test_human_metadata_unknown_specimen_is_not_replication(tmp_path):
    d=tmp_path/'discovery';d.mkdir()
    for f in ['split_genome_audit.sam','split_transcript_audit.sam','LongGF.log']:(d/f).touch()
    gtf=tmp_path/'a.gtf';gtf.write_text('')
    rules=tmp_path/'rules';rules.write_text('frozen')
    summary=assess(d,gtf,tmp_path/'out',sample_id='K562_A',biological_sample_id=None,reference_build='GRCh38/test',rules_path=rules)
    assert summary['sample_id']=='K562_A' and summary['biological_samples'] is None
    assert summary['reference_build']=='GRCh38/test'
