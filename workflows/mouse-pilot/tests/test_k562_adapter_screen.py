import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('k562_adapter',Path(__file__).parents[1]/'scripts/k562/adapter_origin.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def test_internal_core_and_reverse_complement_coordinates():
 core=a.CORES['RTA_A']
 for sequence in [core,a.revcomp(core)]:
  result=a.screen('C'*100+sequence+'G'*100,[110,110])
  hits=[h for h in result['adapter_core_hits'] if h['internal_near_join_flag'] and h['edits']==0]
  assert hits and hits[0]['start']==100 and hits[0]['end']==100+len(core)

def test_indels_are_supported_but_terminal_hits_not_internal():
 core=a.CORES['RTA_A'];mutated=core[:9]+'A'+core[9:18]+core[19:]
 assert a.screen('C'*100+mutated+'G'*100,[110,110])['internal_adapter_near_join']
 assert not a.screen(core+'G'*150,[10,10])['internal_adapter_near_join']
 assert not a.screen('N'*250,[125,125])['internal_adapter_near_join']

def test_internal_polyat_is_a_flag_not_an_origin_verdict():
 r=a.screen('C'*100+'A'*12+'G'*100,[110,110])
 assert r['internal_polyAT_near_join']==[{'start':100,'end':112,'base':'A','length':12}]
 assert r['artifact_truth']=='UNKNOWN' and r['raw_signal_assessment']=='NOT_PERFORMED'
