"""Link frozen structure records to verified reference-assisted exon annotations."""
import base64,gzip,hashlib,json,re
from dashboard_reference_control import control_annotation
from pathlib import Path
AMINO=dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(),'ARNDCQEGHILKMFPSTWYV'))
BASE=Path(__file__).resolve().parent
ROOT=BASE/'source'
a=json.loads((BASE/'inputs/exon_annotations_20260920.json').read_text())
a['candidates'].append(control_annotation())
old=(ROOT/'predicted-structures.html').read_text()
records=json.loads(re.search(r'<script type="application/json" id="chrna-structure-data">(.*?)</script>',old,re.S)[1])
by_name={r['name']:r for r in records}
by_name[a['candidates'][-1]['name']]=records[-1]
assert records[-1]['order']==99
ordered=[]
for d in a['candidates']:
    r=by_name[d['name']]
    pdb=gzip.decompress(base64.b64decode(r['pdb'])).decode()
    residues={}
    for line in pdb.splitlines():
        if line.startswith('ATOM  '): residues[(line[21],int(line[22:26]))]=line[17:20]
    assert list(residues)==[('A',i+1) for i in range(d['length_aa'])],d['name']
    protein=''.join(AMINO[v] for v in residues.values())
    assert len(protein)==r['length']==d['length_aa']==len(r['plddt'])
    assert 'protein_'+hashlib.sha256(protein.encode()).hexdigest()==d['protein_id'],d['name']
    assert d['orf']['stop_start']-d['orf']['start']==3*len(protein)
    ordered.append(r)
    print(d['name'],len(protein),'PDB sequence SHA256 matches frozen protein ID')
old=(ROOT/'annotated-exon-template.html').read_text()
js=re.search(r'<script>\s*(.*?)\s*</script>',old,re.S)[1]
js=js.replace("const W=Math.max(260,root.getBoundingClientRect().width)","const W=Math.max(260,chart.getBoundingClientRect().width)")
js=js.replace('let candidate=8, choices=[0,0];', 'let candidate=10, choices=[0,0];')
js=js.replace('${d.read_count} supporting read · reference-assisted reconstruction', '${d.reference_control?d.status_label:d.read_count+" supporting read · reference-assisted reconstruction"}')
js=js.replace("choices[i]===0?'Default is a display choice; '", "current().reference_control?'Published-architecture reference transcript.':choices[i]===0?'Default is a display choice; '")
js=js.replace('drawRNA(W);}', 'drawRNA(W);proteinTrack();}')
js=js.replace('root.dataset.candidate=String(candidate);}', 'root.dataset.candidate=String(candidate);syncStructure();}')
# The RNA overview uses the same fourth category as the protein for non-exonic bases.
needle='const mid=x((j[0]+j[1])/2);'
injection="d.arms.forEach((a,i)=>{const offset=i?j[1]+Math.min(0,d.query_gap):0;for(const s of a.choices[choices[i]].segments){if(s.kind!=='exon')out+=`<rect x=\"${x(offset+s.rna_start)}\" y=\"${top}\" width=\"${Math.max(1,x(offset+s.rna_end)-x(offset+s.rna_start))}\" height=\"24\" fill=\"var(--viz-series-4)\"/>`;}});"
js=js.replace(needle,injection+needle)
js=js.replace('privateContent:{candidate,choices}', 'privateContent:{candidate,choices,focus,representation:root.querySelector("#linked-style").value}')
addon=(ROOT/'combined-structure-addon.js').read_text()
js=js.replace("picker.addEventListener('change'",addon+"\npicker.addEventListener('change'",1)
js=js.replace('}});render();','}});render();initStructure();')
t=(ROOT/'combined-dashboard-template.html').read_text()
t=t.replace('__ANNOTATION_DATA__',json.dumps(a,separators=(',',':'))).replace('__STRUCTURES__',json.dumps(ordered,separators=(',',':'))).replace('__MAIN_SCRIPT__',js)
assert len(t.encode())<1_000_000
import html
inner=(ROOT/'frame-template.html').read_text().replace('__DASHBOARD_FRAGMENT__',t)
shell=(ROOT/'shell-template.html').read_text().replace('__DASHBOARD_FRAME__',html.escape(inner))
(BASE/'index.html').write_text(shell)
print('Dashboard bytes:',len(t.encode()))
