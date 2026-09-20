"""Adapt the separately reconstructed literature control for the linked viewer."""
import json,re
from pathlib import Path

def control_annotation():
    path=(Path(__file__).resolve().parent/'inputs/provenance.json')
    p=json.loads(path.read_text());c=p['chosen_reconstruction']
    trace=json.loads((Path(__file__).resolve().parent/'inputs/flagship_stage_trace.json').read_text())
    assert p['not_de_novo_recovered'] and not trace['assessment_junctions'] and not trace['selected_protein_ids']
    arms=[]
    for i,gene in enumerate(('Gsdmd','Tmem106a')):
        exons=[e for e in c['exon_path'] if e['gene']==gene];segments=[];offset=0
        for j,e in enumerate(exons):
            n=e['end']-e['start']
            segments.append(dict(start=e['start'],end=e['end'],rna_start=offset,rna_end=offset+n,block=j+1,kind='exon',number=e['exon_number'],exon_id=re.search(r'exon_id "([^"]+)"',e['source_line'])[1],source_row=e['source_row'],partial=False))
            offset+=n
        txname=re.search(r'transcript_name "([^"]+)"',exons[0]['source_line'])[1]
        tx=dict(id=c['parent_transcripts'][i],name=txname,segments=segments,covered_nt=offset,projected_nt=offset,nonexonic_nt=0)
        arms.append(dict(gene=gene,chromosome=exons[0]['chromosome'],strand=exons[0]['strand'],biotype='protein_coding',blocks=[[e['start'],e['end']] for e in exons],choices=[tx],equally_scored_transcripts=1))
    assert arms[0]['choices'][0]['projected_nt']==c['junction_offset']
    assert sum(a['choices'][0]['projected_nt'] for a in arms)==len(c['rna'])
    return dict(name='Gsdmd → Tmem106a · literature reference control',order=99,protein_id='protein_'+p['protein_sha256'],read_id=None,read_count=None,sequence_source='literature_reference_reconstruction',length_nt=len(c['rna']),length_aa=p['amino_acids'],orf=c['orf'],junction=[c['junction_offset']]*2,query_gap=0,arms=arms,reference_control=True,algorithm_recovered=False,provenance='inputs/provenance.json',status_label='Literature reference reconstruction · NOT recovered by the pilot algorithm (SRR28984805)')
