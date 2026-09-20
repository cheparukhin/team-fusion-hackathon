import csv,json,pathlib,xml.etree.ElementTree as E
R=pathlib.Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((R/'manifest/liver_runs.tsv').open(),delimiter='\t'))
donors={'SRR31438987':'human_C710121','SRR31438990':'human_C710121','SRR31438989':'human_HR-314-D1','SRR31438988':'human_ATR1234149-50','SRR31429656':'mouse_Tissue7','SRR31429655':'mouse_Tissue6','SRR31429713':'mouse_Tissue12','SRR31429688':'cow_BR-314-D1','SRR31429687':'cow_BR-314-D2','SRR31429701':'rat_Tissue26','SRR31429700':'rat_Tissue21'}
for r in rows:
 x=E.parse(R/'manifest'/f"{r['run_accession']}_ncbi.xml").getroot()
 r['scientific_name']=x.findtext('.//SAMPLE_NAME/SCIENTIFIC_NAME') or r['scientific_name']
 r['tax_id']=x.findtext('.//SAMPLE_NAME/TAXON_ID') or r['tax_id']
 r['sample_title']=x.findtext('.//SAMPLE/TITLE') or r['sample_title']
 run=x.find('.//RUN'); r['ncbi_read_count']=run.get('total_spots','')
 r['biological_sample_id']=donors.get(r['run_accession'],'UNRESOLVED')
 r['replicate_identity_status']='source_reconciled' if r['run_accession'] in donors else 'conflicting_donor_and_tissue_metadata'
 r['metadata_note']=''
 if 'Rattus' in r['scientific_name']:r['metadata_note']='Supplement read totals appear swapped between AR47/48 and AR49/50; use original deposited identifiers; not counts alone.'
 if 'Canis' in r['scientific_name']:r['metadata_note']='Dog donor labels conflict; AR96/97 combined; AR60 appears under Testis in supplement despite liver filename. Exclude from strict replicated set.'
 if r['run_accession'] in ['SRR31438987','SRR31438990']:r['metadata_note']='Technical sequencing runs of the same biological donor; collapse biological replication.'
 r['source_original_files']=';'.join(i.get('filename','') for i in x.findall('.//SRAFile') if i.get('filename','').endswith(('.fastq.gz','.fq.gz')))
with (R/'manifest/samples.tsv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
refs=[]
for s in json.loads((R/'manifest/reference_urls.json').read_text()):
 sp=s['species'];urls=s[f'fasta/{sp}/dna/'];fa=next((u for u in urls if u.endswith('.dna.primary_assembly.fa.gz')),next(u for u in urls if u.endswith('.dna.toplevel.fa.gz')));gtf=s[f'gtf/{sp}/'][0]
 refs.append({'species':sp,'release':115,'genome_url':fa,'gtf_url':gtf,'assembly':fa.split('/')[-1].split('.dna.')[0].split('.',1)[1]})
(R/'manifest/references.json').write_text(json.dumps(refs,indent=2))
print([(r['run_accession'],r['scientific_name'],r['biological_sample_id']) for r in rows])
