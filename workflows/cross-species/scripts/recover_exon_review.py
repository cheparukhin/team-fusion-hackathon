"""Bounded recovery from saved BLAST hits; original failed outputs remain intact."""
import pathlib,sys,csv,json,re,yaml,logging,time
import pandas as pd
R=pathlib.Path(__file__).resolve().parents[1];sp,run=sys.argv[1:3];out=R/'per_species'/sp/run;src=out/'reconstruction_longgf_only/exon_repair';review=out/'review_reconstruction';work=review/'exon_repair';work.mkdir(parents=True,exist_ok=True)
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');sys.path.insert(0,str(R/'software/TYPHON'))
from typhon.modules.exon_repair.exon_data_processing import run_phase4_exon_processing
from typhon.modules.exon_repair import SequenceReconstructor
cfg=yaml.safe_load((out/'config.yaml').read_text());cfg['project']['output_dir']=str(review)
selected=pd.read_csv(src/'ordered_blast_results.csv');names=set(selected['Transcript_ID']);bed=work/'selected_exons.numeric_exon_number.bed';n=0
with (src/'modified_exon_repair/all_exons.bed').open() as f,bed.open('w') as dst:
 for l in f:
  if '\texon\t' not in l:continue
  m=re.search(r'transcript_name "([^"]+)"',l)
  if m and m.group(1) in names:
   dst.write(re.sub(r'exon_number "(\d+)";',r'exon_number \1;',l));n+=1
fix={'scope':'LongGF-only reference-assisted reconstruction from completed BLAST hits','reason':'TYPHON regex only parses unquoted exon_number; valid native GTF values were quoted, causing all exons to be dropped','transformation':'Selected-transcript BED only: exon_number "N" -> exon_number N; coordinates, transcript IDs, sequence and exon numbers unchanged','selected_exon_rows':n,'original_failure_preserved':str(src)}
(work/'compatibility_fix.json').write_text(json.dumps(fix,indent=2))
p4=run_phase4_exon_processing(selected,str(bed),str(work),cfg)
lib=pd.read_csv(src/'chimera_library.csv');p5=SequenceReconstructor(cfg,str(review)).reconstruct_sequences(p4,lib)
(review/'result.json').write_text(json.dumps({'status':'reference-assisted reconstructed models; biological validation pending','statistics':p5['statistics'],'table':p5['final_chimeras_path'],'fasta':p5['reconstructed_sequences'],'caller_scope':'LongGF only','Genion':'not integrated','JAFFAL':'unavailable','conservation':'not established'},indent=2,default=str))
