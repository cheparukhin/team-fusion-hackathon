"""Synthetic technical controls only: never part of biological candidate tables."""
import pathlib,random,subprocess,json
R=pathlib.Path(__file__).resolve().parents[1];out=R/'qc/synthetic_controls';out.mkdir(exist_ok=True);random.seed(1729)
seqs={};gtf=[]
for chrom,gene in [('SYNTHETIC1','SYNTHETIC_GENE_A'),('SYNTHETIC2','SYNTHETIC_GENE_B')]:
 s=''.join(random.choice('ACGT') for _ in range(3000));s=s[:1000]+'GT'+s[1002:1498]+'AG'+s[1500:];seqs[chrom]=s
 gtf.append(f'{chrom}\ttest\tgene\t401\t2100\t.\t+\t.\tgene_id "{gene}"; gene_name "{gene}"; gene_type "protein_coding"; gene_biotype "protein_coding";')
 for start,end in [(401,1000),(1501,2100)]:gtf.append(f'{chrom}\ttest\texon\t{start}\t{end}\t.\t+\t.\tgene_id "{gene}"; transcript_id "{gene}_T"; gene_name "{gene}"; gene_type "protein_coding";')
(out/'genome.fa').write_text(''.join('>'+k+'\n'+v+'\n' for k,v in seqs.items()));(out/'genes.gtf').write_text('\n'.join(gtf)+'\n')
a=seqs['SYNTHETIC1'];b=seqs['SYNTHETIC2']
for label,reads in [('positive',[a[400:1000]+b[1500:2100]]*3),('negative',[a[400:1000]+a[1500:2100],b[400:1000]+b[1500:2100]])]:
 fq=out/(label+'.fastq');fq.write_text(''.join(f'@SYNTHETIC_{label}_{i}\n{s}\n+\n'+('I'*len(s))+'\n' for i,s in enumerate(reads)))
 with (out/(label+'.alignment.log')).open('w') as err:
  subprocess.run(['minimap2','-ax','splice','-uf','-k14','--secondary=no','-G','50k','-t','2',str(out/'genome.fa'),str(fq),'-o',str(out/(label+'.sam'))],check=True,stderr=err)
 subprocess.run(['samtools','sort','-n','-o',str(out/(label+'.bam')),str(out/(label+'.sam'))],check=True)
 with (out/(label+'.longgf.log')).open('w') as log:subprocess.run(['LongGF',str(out/(label+'.bam')),str(out/'genes.gtf'),'100','50','100','2','0','1','16'],check=True,stdout=log,stderr=subprocess.STDOUT)
pos=(out/'positive.longgf.log').read_text();neg=(out/'negative.longgf.log').read_text()
assert any(l.startswith('GF') for l in pos.splitlines()),'Positive fusion not detected'
assert not any(l.startswith('GF') for l in neg.splitlines()),'Fusion called in negative control'
assert all('SYNTHETIC_positive_'+str(i) in pos for i in range(3)),'Read identity lost'
(out/'result.json').write_text(json.dumps({'status':'passed','biological_evidence':False,'positive_reads':3,'negative_reads':2,'seed':1729},indent=2))
print('PASS synthetic LongGF positive/negative/read-ID controls')
