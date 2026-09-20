"""Reversible native-Ensembl annotation adapter for TYPHON's GENCODE-style names.
Coordinates, gene IDs, transcript IDs and strand are never translated.
"""
import argparse,csv,json,pathlib,re,subprocess

def attrs(s):return dict(re.findall(r'(\S+) "([^"]*)"',s))
def adapt(genome,gtf,out):
 out.mkdir(parents=True,exist_ok=True)
 subprocess.run(['samtools','faidx',str(genome)],check=True)
 contigs={l.split('\t')[0] for l in pathlib.Path(str(genome)+'.fai').open()}
 transcripts={};genes={};skipped={};kept=0
 with gtf.open() as src,(out/'typhon.gtf').open('w') as dst:
  for line in src:
   if line.startswith('#'):dst.write(line);continue
   f=line.rstrip('\n').split('\t');a=attrs(f[8]);gid=a.get('gene_id');tid=a.get('transcript_id')
   if f[0] not in contigs:skipped[f[0]]=skipped.get(f[0],0)+1;continue
   if not gid:raise ValueError('Missing gene_id')
   genes.setdefault(gid,{'gene_id':gid,'original_gene_name':a.get('gene_name',''),'gene_biotype':a.get('gene_biotype',a.get('gene_type','unknown'))})
   a['gene_name']=gid;a['gene_type']=a.get('gene_biotype',a.get('gene_type','unknown'))
   if tid:
    if tid not in transcripts:
     transcripts[tid]={'transcript_id':tid,'gene_id':gid,'original_transcript_name':a.get('transcript_name',''),'typhon_transcript_name':gid+'-'+str(len(transcripts)+1),'transcript_type':a.get('transcript_biotype',a.get('transcript_type','unknown'))}
    a['transcript_name']=transcripts[tid]['typhon_transcript_name'];a['transcript_type']=transcripts[tid]['transcript_type']
   f[8]=' '.join(f'{k} "{v}";' for k,v in a.items());dst.write('\t'.join(f)+'\n');kept+=1
 for name,records in [('gene_names',genes),('transcript_names',transcripts)]:
  with (out/(name+'.tsv')).open('w') as f:
   w=csv.DictWriter(f,fieldnames=list(next(iter(records.values()))),delimiter='\t');w.writeheader();w.writerows(records.values())
 subprocess.run(['gffread',str(out/'typhon.gtf'),'-g',str(genome),'-w',str(out/'native_transcripts.fa')],check=True)
 count=0
 with (out/'native_transcripts.fa').open() as src,(out/'typhon_transcripts.fa').open('w') as dst:
  for line in src:
   if line.startswith('>'):
    tid=line[1:].split()[0];t=transcripts[tid];g=t['gene_id'];name=t['typhon_transcript_name']
    dst.write(f'>{tid}|{g}|-| -|{name}|{g}|0|{t["transcript_type"]}|\n'.replace('| -|','|-|'));count+=1
   else:dst.write(line)
 (out/'adapter_qc.json').write_text(json.dumps({'native_genome':str(genome),'native_gtf':str(gtf),'retained_features':kept,'transcripts_extracted':count,'annotated_transcripts':len(transcripts),'excluded_contigs':skipped,'coordinate_transform':'none; 1-based closed native GTF unchanged','gene_names':'Stable IDs used internally; reversible original names TSV','limitations':'FASTA length field placeholder 0 until corrected below'},indent=2))
 # Rewrite headers with exact transcript lengths; preserve native exon-derived sequence.
 p=out/'typhon_transcripts.fa';items=[];header=None;seq=[]
 for line in p.open():
  if line.startswith('>'):
   if header:items.append((header,''.join(seq)))
   header=line.strip().split('|');seq=[]
  else:seq.append(line.strip())
 if header:items.append((header,''.join(seq)))
 with p.open('w') as f:
  for h,s in items:h[6]=str(len(s));f.write('|'.join(h)+'\n'+s+'\n')
 q=json.loads((out/'adapter_qc.json').read_text());q.pop('limitations');(out/'adapter_qc.json').write_text(json.dumps(q,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('genome',type=pathlib.Path);p.add_argument('gtf',type=pathlib.Path);p.add_argument('out',type=pathlib.Path);a=p.parse_args();adapt(a.genome,a.gtf,a.out)
