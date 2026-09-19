"""Match genuine STAR/Parabricks junctions to sequence-mapped probe endpoints.

STAR columns2/5 are1-based intronic bases; convert to terminal exonic bases.
Require chromosomes, canonical ordered parent orientation, strands and both endpoints
within10nt. Support is a read-ID set, not a junction-line count. A zero means
not found in this bounded sample, never a biological negative.
"""
import argparse,hashlib,json,pathlib
import pandas as pd

def terminal_coordinates(donor, donor_strand, acceptor, acceptor_strand):
    if donor_strand not in ('+','-') or acceptor_strand not in ('+','-'):
        raise ValueError('strands must be + or -')
    return int(donor)-(1 if donor_strand=='+' else -1),int(acceptor)+(1 if acceptor_strand=='+' else -1)

def match(probes, lines, tolerance=10):
    if tolerance <0:raise ValueError('negative tolerance')
    evidence=[]
    for line in lines:
        if not line.strip() or line.startswith('#'):continue
        cols=line.rstrip().split('\t')
        if len(cols)<10:continue
        c1,p1,s1,c2,p2,s2=cols[:6]
        try:
            if int(cols[6]) < 0:continue  # encompassing mate pairs do not resolve a junction
            b1,b2=terminal_coordinates(p1,s1,p2,s2)
        except (ValueError,TypeError):continue
        flip={'+':'-','-':'+'}
        orientations=[(c1,b1,s1,c2,b2,s2,int(p1),int(p2),'direct'),
                      (c2,b2,flip[s2],c1,b1,flip[s1],int(p2),int(p1),'reverse_complement')]
        for row in probes.itertuples():
            for ac1,ab1,as1,ac2,ab2,as2,ip1,ip2,orientation in orientations:
                if (row.chrom1,row.strand1,row.chrom2,row.strand2)!=(ac1,as1,ac2,as2):continue
                if abs(int(row.breakpoint1)-ab1)<=tolerance and abs(int(row.breakpoint2)-ab2)<=tolerance:
                    evidence.append(dict(pair_id=row.pair_id,probe_id=row.probe_id,read_id=cols[9],chrom1=ac1,star_intron1=ip1,terminal1=ab1,strand1=as1,chrom2=ac2,star_intron2=ip2,terminal2=ab2,strand2=as2,offset1=ab1-int(row.breakpoint1),offset2=ab2-int(row.breakpoint2),assembly='GRCm39',match_orientation=orientation,raw_star_chrom1=c1,raw_star_intron1=int(p1),raw_star_strand1=s1,raw_star_chrom2=c2,raw_star_intron2=int(p2),raw_star_strand2=s2))
    return evidence

def main():
    p=argparse.ArgumentParser();p.add_argument('--junctions',type=pathlib.Path,required=True);p.add_argument('--probes',type=pathlib.Path,default=pathlib.Path('results/dataset_reconstruction/probe_junctions.tsv'));p.add_argument('--read-pairs',type=int,default=200000);p.add_argument('--output',type=pathlib.Path,default=pathlib.Path('results/compute'));a=p.parse_args()
    probes=pd.read_csv(a.probes,sep='\t');assert set(probes.assembly)=={'GRCm39'}
    rows=match(probes,a.junctions.read_text().splitlines());a.output.mkdir(parents=True,exist_ok=True)
    fields=['pair_id','probe_id','read_id','chrom1','star_intron1','terminal1','strand1','chrom2','star_intron2','terminal2','strand2','offset1','offset2','assembly','match_orientation','raw_star_chrom1','raw_star_intron1','raw_star_strand1','raw_star_chrom2','raw_star_intron2','raw_star_strand2']
    raw=pd.DataFrame(rows,columns=fields).drop_duplicates()
    raw.to_csv(a.output/'parabricks_junction_matches_raw.tsv',sep='\t',index=False)
    raw.drop_duplicates(['pair_id','probe_id','read_id','chrom1','terminal1','strand1','chrom2','terminal2','strand2']).to_csv(a.output/'parabricks_junction_matches.tsv',sep='\t',index=False)
    support={pair:sorted({r['read_id'] for r in rows if r['pair_id']==pair}) for pair in probes.pair_id.unique()}
    pd.DataFrame([dict(pair_id=k,parabricks_support=len(v),parabricks_read_ids=json.dumps(v),parabricks_status='observed_support' if v else f'not_detected_in_{a.read_pairs}_pair_pilot',run_accession='SRR37513722',assembly='GRCm39') for k,v in support.items()]).to_csv(a.output/'parabricks_evidence.tsv',sep='\t',index=False)
    (a.output/'match_manifest.json').write_text(json.dumps(dict(tolerance_nt=10,coordinate_rule='STAR intronic donor minus strand direction; acceptor plus strand direction; compare ordered exonic terminal bases in direct or reverse-complement-equivalent read orientation; canonical parent order retained and raw STAR order saved',junction_type_rule='Require split junction type>=0; exclude encompassing-mate type-1',star_format_source='https://github.com/alexdobin/STAR/blob/2.7.2a/extras/doc-latex/STARmanual.tex',junction_sha256=hashlib.file_digest(a.junctions.open('rb'),'sha256').hexdigest(),probe_sha256=hashlib.file_digest(a.probes.open('rb'),'sha256').hexdigest(),matched_pairs=sum(bool(v) for v in support.values()),unique_read_ids=len({r['read_id'] for r in rows})),indent=2))
if __name__=='__main__':main()
