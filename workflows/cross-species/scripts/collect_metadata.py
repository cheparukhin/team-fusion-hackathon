#!/usr/bin/env python3
"""Cache public metadata without changing biological identity or inventing accessions."""
from pathlib import Path
import csv,json,requests,concurrent.futures,hashlib,datetime,xml.etree.ElementTree as ET,zipfile,io
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'manifest'; (M/'xml').mkdir(exist_ok=True)
rows=list(csv.DictReader((M/'ena_response.tsv').open(),delimiter='\t'))
liver=[r for r in rows if 'liver' in r['experiment_title'].lower() and 'rooster' not in r['experiment_title'].lower()]
def get(task):
 name,url=task;p=M/name
 if p.exists():return name,'cached'
 r=requests.get(url,timeout=60);r.raise_for_status();p.write_bytes(r.content)
 return name,r.status_code
jobs=[]
for r in liver:
 for typ,acc in [('experiment',r['experiment_accession']),('sample',r['secondary_sample_accession']),('run',r['run_accession'])]:
  jobs.append((f'xml/{acc}.xml','https://www.ebi.ac.uk/ena/browser/api/xml/'+acc))
jobs.append(('supplement_dataset1.xlsx','https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-72124-1/MediaObjects/41467_2026_72124_MOESM4_ESM.xlsx'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for f in [ex.submit(get,j) for j in jobs]:
  try: print(f.result(),flush=True)
  except Exception as e:print(type(e).__name__,str(e),flush=True)
# Decode xlsx using stdlib to avoid an installation just for metadata.
p=M/'supplement_dataset1.xlsx'
if p.exists():
 ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 with zipfile.ZipFile(p) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
  for sheet in z.namelist():
   if sheet.startswith('xl/worksheets/sheet') and sheet.endswith('.xml'):
    lines=[]
    for row in ET.fromstring(z.read(sheet)).findall('.//s:row',ns):
     line=[]
     for c in row.findall('s:c',ns):
      v=c.find('s:v',ns);val=v.text if v is not None else ''
      if c.attrib.get('t')=='s':val=ss[int(val)]
      elif c.attrib.get('t')=='inlineStr':val=''.join(c.find('s:is',ns).itertext())
      line.append(c.attrib.get('r','')+'='+str(val))
     lines.append('\t'.join(line))
    (M/(Path(sheet).stem+'.tsv')).write_text('\n'.join(lines)+'\n')
for r in liver:
 p=M/'xml'/f"{r['secondary_sample_accession']}.xml"
 if p.exists():
  e=ET.parse(p)
  r['scientific_name']=e.findtext('.//SCIENTIFIC_NAME') or r['scientific_name']
  r['tax_id']=e.findtext('.//TAXON_ID') or r['tax_id']
  attrs={a.findtext('TAG'):a.findtext('VALUE') for a in e.findall('.//SAMPLE_ATTRIBUTE')}
  r['sample_attributes']=json.dumps(attrs,sort_keys=True)
  r['sample_title']=e.findtext('.//TITLE') or r['sample_title']
 r['availability']='ENA_FASTQ_listed' if r['fastq_ftp'] else 'ENA_FASTQ_unavailable_check_SRA'
 r['replicate_identity_status']='pending_supplement_and_donor_reconciliation'
with (M/'liver_runs.tsv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in liver for k in r)),delimiter='\t');w.writeheader();w.writerows(liver)
checks=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in M.rglob('*') if p.is_file() and p.name!='checksums.json']
(M/'checksums.json').write_text(json.dumps(checks,indent=2))
print('liver_runs',len(liver),'listed_fastq_bytes',sum(int(r['fastq_bytes'] or 0) for r in liver))
