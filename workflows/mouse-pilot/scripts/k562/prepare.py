"""Pin small public metadata before candidate inspection; no raw archives."""
import csv,io,json,hashlib,urllib.request,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'runs/k562-pilot/20260919-overnight';M=RUN/'metadata';M.mkdir(exist_ok=True)
def fetch(url,name):
 data=urllib.request.urlopen(url,timeout=45).read();(M/name).write_bytes(data);return data
commit=json.loads(fetch('https://api.github.com/repos/GoekeLab/sg-nex-data/commits/master','sgnex-commit.json'))['sha']
selected=[]
for file in ['samples.tsv','illumina_samples.tsv']:
 data=fetch(f'https://raw.githubusercontent.com/GoekeLab/sg-nex-data/{commit}/docs/{file}',file)
 for n,row in enumerate(csv.DictReader(io.StringIO(data.decode()),delimiter='\t'),2):
  if row['sample_alias'] in ['SGNex_K562_directRNA_replicate4_run1','SGNex_K562_directRNA_replicate5_run1','SGNex_K562_Illumina_replicate4_run1']:
   selected.append({'source_file':file,'source_row':n,'row':row,'biological_specimen_id':None,'relationship_status':'UNKNOWN: distinct source library aliases; no extraction/culture crosswalk verified'})
base='https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/'
md5=fetch(base+'MD5SUMS','gencode43-MD5SUMS').decode(); names=['GRCh38.primary_assembly.genome.fa.gz','gencode.v43.annotation.gtf.gz','gencode.v43.transcripts.fa.gz']
refs=[]
for n in names:
 matches=[line.split()[0] for line in md5.splitlines() if line.split()[-1].lstrip('./')==n]
 assert len(matches)==1,(n,matches)
 refs.append({'name':n,'url':base+n,'md5':matches[0]})
config={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sgnex_commit':commit,'samples':selected,'references':refs,'reference_build':'GRCh38.p13/GENCODE43','sequin_commit':'d9f3cfabd3c1593ff94b4fdd00b344aff71d3c07','sequin_files':['rnasequin_decoychr_2.4.fa','rnasequin_sequences_2.4.fa'],'sequin_note':'Published RNA sequin 2.4 decoy; mixture-version equivalence not established. Decoy/mixed assignments excluded from human labels.','star_commit':'b1edc1208d91a53bf40ebae8669f71d50b994851','threads':14,'incremental_compute_cap_usd':20,'max_worker_hours':8,'checkpoint_a_seconds':14400,'checkpoint_b_seconds':14400,'read_subset_rule':'SHA256(original_read_id) first byte equals 0; selected before outcomes','longread_settings':{'minimap2':'2.24','LongGF':'0.1.2','genome':['-ax','splice','-uf','-k14','-G50k'],'audit':['--MD','--secondary=yes','-N50','-p0.1']},'illumina_rules':{'STAR':'2.7.11b','min_segment':20,'min_junction_overhang':20,'max_chimeric_mappings':1,'max_score_drop':20,'min_score_separation':10,'max_mismatch_fraction':0.04,'exact_support':'canonical orientable split junction; zero reported repeat ambiguity; chimeric score exceeds nonchimeric by >=10; distinct read-pair names; no molecule-count claim','unstranded':'Use STAR junction motif to resolve transcript order; noncanonical orientation remains unresolved','duplicate_policy':'distinct fragment IDs and alignment-geometry counts; PCR duplicates not resolved without UMIs'}}
(RUN/'config.json').write_text(json.dumps(config,indent=2)+'\n')
fetch(f'https://raw.githubusercontent.com/GoekeLab/sg-nex-data/{commit}/README.md','SGNEX_README.md')
print(json.dumps({'run':str(RUN),'commit':commit,'samples':[x['row']['sample_alias'] for x in selected],'refs':refs},indent=2))
