"""Run the real pinned tools and assessor on deterministic technical controls."""
import json
import os
from pathlib import Path
import random
import subprocess

from chrna.pilot_assessment import assess

root=Path(__file__).resolve().parents[1]
base=root/'runs/focused-pilot-20260919/technical-controls'
base.mkdir(parents=True,exist_ok=True)
binary=root/'runs/focused-pilot-20260919/bundle/tools/bin'
env=os.environ.copy()
env['LD_LIBRARY_PATH']=str(binary.parent/'lib')
rng=random.Random(719)
a=''.join(rng.choices('ACGT',k=5000)); b=''.join(rng.choices('ACGT',k=5000))
fusion=a[1100:1400]+b[2200:2500]
(base/'genome.fa').write_text('>chrA\n'+a+'\n>chrB\n'+b+'\n')
(base/'reads.fastq').write_text('@synthetic_positive_1\n'+fusion+'\n+\n'+'I'*600+'\n@synthetic_single_transcript_control\n'+a[1100:1700]+'\n+\n'+'I'*600+'\n')
gtf=[]
for chrom,gene,start,end in [('chrA','A',1001,1800),('chrB','B',2001,2800)]:
    for feature in ('gene','transcript','exon'):
        gtf.append(f'{chrom}\tsynthetic\t{feature}\t{start}\t{end}\t.\t+\t.\tgene_id "{gene}"; transcript_id "{gene}.1"; gene_name "{gene}"; gene_type "protein_coding";')
(base/'annotation.gtf').write_text('\n'.join(gtf)+'\n')
commands=[]
def run(argv, log, stdout=None):
    commands.append(argv)
    with (base/log).open('w') as err:
        if stdout:
            with stdout.open('w') as out:
                subprocess.run(argv,env=env,stdout=out,stderr=err,check=True)
        else:
            subprocess.run(argv,env=env,stderr=err,check=True)

run([str(binary/'minimap2'),'-ax','splice','-uf','-k14','--MD','--secondary=yes','-N50','-p0.1','-G50k','-t2',str(base/'genome.fa'),str(base/'reads.fastq'),'-o',str(base/'split_genome_audit.sam')],'genome.log')
run([str(binary/'samtools'),'sort','-n','-o',str(base/'reads.bam'),str(base/'split_genome_audit.sam')],'sort.log')
run([str(binary/'LongGF'),str(base/'reads.bam'),str(base/'annotation.gtf'),'100','50','100','2','0','1','0'],'LongGF.stderr.log',base/'LongGF.log')
parents='>A_transcript\n'+a[1000:1800]+'\n>B_transcript\n'+b[2000:2800]+'\n'
summaries={}
for case,extra in [('two_gene_supported',''),('known_noncoding_explanation','>known_lncRNA_transcript\n'+fusion+'\n')]:
    tx=base/f'{case}.transcripts.fa'
    tx.write_text(parents+extra)
    run([str(binary/'minimap2'),'-ax','map-ont','-k14','--MD','--secondary=yes','-N50','-p0.1','-t2',str(tx),str(base/'reads.fastq'),'-o',str(base/'split_transcript_audit.sam')],case+'.minimap2.log')
    target=base/case
    summaries[case]=assess(base,base/'annotation.gtf',target)
    (target/'split_transcript_audit.sam').write_bytes((base/'split_transcript_audit.sam').read_bytes())
    rows=json.loads((target/'read_decisions.json').read_text())
    expected='supported_two_gene_junction' if not extra else 'single_transcript_explained'
    assert len(rows)==1,rows
    assert rows[0]['read_id']=='synthetic_positive_1' and rows[0]['state']==expected,rows
result={'status':'passed','purpose':'Technical positive and known-single-transcript explanation controls, not biological negative labels','cases':summaries,'commands':commands}
(base/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'passed','cases':list(summaries)},indent=2))
