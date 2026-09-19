"""External-library corroboration; no fitting or biological negative labels."""
import collections,csv,hashlib,html,json
from pathlib import Path

def key(r):
    return (r['chromosome_5p'],r['boundary_5p'],r['strand_5p'],r['chromosome_3p'],r['boundary_3p'],r['strand_3p'])

def star_key(fields):
    """STAR intronic 1-based coordinates to exon-boundary interbase coordinates.

    Type 2 motif is antisense: reverse segment order and both strands.
    Noncanonical/discordant records cannot establish transcript order here.
    """
    f=fields;t=int(f[6])
    if t not in (1,2):return None
    donor=int(f[1])-(f[2]=='+'); acceptor=int(f[4])-(f[5]=='-')
    if t==1:return (f[0],donor,f[2],f[3],acceptor,f[5])
    flip={'+':'-','-':'+'}
    return (f[3],acceptor,flip[f[5]],f[0],donor,flip[f[2]])

def expected_top(rows,positives,k,baseline=False):
    if not rows:return {'k':0,'expected_supported':None,'fraction':None}
    k=min(k,len(rows));groups=collections.defaultdict(list)
    for r in rows:
        group=(-r['distinct_qualifying_reads'],) if baseline else (r['rank_min'],r['rank_max'])
        groups[group].append(r)
    total=0.;slots=k
    for g in sorted(groups):
        rs=groups[g];take=min(slots,len(rs));total+=take*sum(r['junction_id'] in positives for r in rs)/len(rs);slots-=take
        if slots==0:break
    return {'k':k,'expected_supported':total,'fraction':total/k if k else None}

def compare(a,b):
    # IDs include frozen annotation gene assignments, not just nearby breaks.
    aa={r['junction_id'] for r in a};bb={r['junction_id'] for r in b}
    return {'a':len(aa),'b':len(bb),'intersection':len(aa&bb),'union':len(aa|bb),'a_to_b':len(aa&bb)/len(aa) if aa else None,'b_to_a':len(aa&bb)/len(bb) if bb else None,'ranker_top20':expected_top(a,bb,20),'read_count_top20':expected_top(a,bb,20,True),'interpretation':'Observed corroboration, not biological precision or sensitivity'}

def illumina_evidence(path):
    evidence=collections.defaultdict(set);geometries=collections.defaultdict(set);stats=collections.Counter()
    with open(path) as src:
        for line in src:
            f=line.split()
            if len(f)<14 or f[0].startswith('#'):continue
            try:k=star_key(f)
            except (ValueError,KeyError):continue
            stats['records']+=1
            if k is None:stats['discordant_or_unoriented']+=1;continue
            if int(f[7])+int(f[8])>0:stats['repeat_ambiguous']+=1;continue
            if len(f)<19 or int(f[14])!=1 or int(f[17])-int(f[16])<10:
                stats['ambiguous_or_low_margin']+=1;continue
            evidence[k].add(f[9]);geometries[k].add(tuple(f[10:14]));stats['qualifying_records']+=1
    return evidence,geometries,dict(stats)

def report(base):
    base=Path(base);out=base/'outputs';out.mkdir(exist_ok=True)
    a_name='SGNex_K562_directRNA_replicate4_run1';b_name='SGNex_K562_directRNA_replicate5_run1'
    def load(name):
        p=out/name/'assessment';r=json.loads((p/'rna_ranking.json').read_text());ds=json.loads((p/'read_decisions.json').read_text());names={d['junction_id']:(d['gene_name_5p'],d['gene_name_3p']) for d in ds}
        for x in r:x['pair']=':'.join(names[x['junction_id']])
        return r,ds
    if not (out/a_name/'assessment/rna_ranking.json').exists():return
    aa,ad=load(a_name)
    bb,bd=load(b_name) if (out/b_name/'assessment/rna_ranking.json').exists() else ([],[])
    a=[x for x in aa if x['evidence_state']=='supported_two_gene_junction'];b=[x for x in bb if x['evidence_state']=='supported_two_gene_junction']
    stats=compare(a,b);stats['without_BCR_ABL1']=compare([x for x in a if x['pair']!='BCR:ABL1'],[x for x in b if x['pair']!='BCR:ABL1'])
    stats['strata']={s:compare([x for x in a if (x['chromosome_5p']==x['chromosome_3p'])==cis],[x for x in b if (x['chromosome_5p']==x['chromosome_3p'])==cis]) for s,cis in [('cis',True),('trans',False)]}
    for minimum in [1,2,3]:stats['strata'][f'min_reads_{minimum}']=compare([x for x in a if x['distinct_qualifying_reads']>=minimum],[x for x in b if x['distinct_qualifying_reads']>=minimum])
    ik=out/'illumina/Chimeric.out.junction';ev={};geom={}
    if (out/'illumina/complete.json').exists():
        ev,geom,istats=illumina_evidence(ik);positive={r['junction_id'] for r in a if key(r) in ev}
        stats['illumina']={'status':'processed','statistics':istats,'primary_A_supported':len(positive),'ranker_top20':expected_top(a,positive,20),'read_count_top20':expected_top(a,positive,20,True),'duplicate_resolution':'Fragment IDs and geometry reported; molecular duplicates UNKNOWN'}
    else:stats['illumina']={'status':'NOT_COMPLETED'}
    if stats['illumina']['status']=='processed':
        noncontrol=[r for r in a if r['pair']!='BCR:ABL1']
        stats['illumina']['without_BCR_ABL1']={'primary_A_supported':sum(r['junction_id'] in positive for r in noncontrol),'ranker_top20':expected_top(noncontrol,positive,20),'read_count_top20':expected_top(noncontrol,positive,20,True)}
    stats['biological_independence']='UNKNOWN';stats['adapter_status']='NOT_ASSESSED';stats['origin']='NOT_ASSESSED'
    stats['checkpoint_a']='processed' if (out/b_name/'freeze.json').exists() else 'incomplete'
    (out/'corroboration.json').write_text(json.dumps(stats,indent=2)+'\n')
    controls={}
    for name,rs,ds in [('A',aa,ad),('B',bb,bd)]:
        controls[name]={'ranked_records':[r for r in rs if r['pair']=='BCR:ABL1'],'read_decisions':[d for d in ds if d['gene_name_5p']=='BCR' and d['gene_name_3p']=='ABL1'],'limitation':'DNA fusion detection control; absence is not proof of absence'}
        source=out/(a_name if name=='A' else b_name)/'discovery/LongGF.log'
        controls[name]['caller_pair_lines']=[line for line in source.read_text().splitlines() if 'BCR' in line and 'ABL1' in line] if source.exists() else []
    (out/'bcr_abl1_trace.json').write_text(json.dumps(controls,indent=2)+'\n')
    b_ids={r['junction_id'] for r in b}
    fields=['junction_id','pair','evidence_state','distinct_qualifying_reads','rank_min','rank_max','B_exact_supported','Illumina_fragment_ids','Illumina_distinct_geometries','adapter_status','origin']
    with (out/'primary_candidates.tsv').open('w') as f:
        w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader()
        for r in aa:
            v={c:r.get(c) for c in fields};v.update(B_exact_supported=r['junction_id'] in b_ids,Illumina_fragment_ids=len(ev.get(key(r),[])) if stats['illumina']['status']=='processed' else None,Illumina_distinct_geometries=len(geom.get(key(r),[])) if stats['illumina']['status']=='processed' else None,adapter_status='NOT_ASSESSED',origin='NOT_ASSESSED');w.writerow(v)
    rows=''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in [r['pair'],r['display_rank'],r['distinct_qualifying_reads'],r['junction_id'] in b_ids])+'</tr>' for r in a[:40])
    (out/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>K562 external RNA verification</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto}td,th{padding:8px;border-bottom:1px solid #ccc}pre{white-space:pre-wrap}</style><h1>K562 external RNA verification</h1><p>Human RNA mapping evidence. Biological independence, RNA origin, protein expression and function are not established. Hi-C and structure prediction deferred. Internal-adapter assay not performed. LongGF association is pair-level. This report is a progress snapshot until completion.json and resource shutdown receipts exist.</p><h2>Corroboration</h2><pre>'+html.escape(json.dumps(stats,indent=2))+'</pre><h2>Primary library candidates</h2><table><tr><th>Pair</th><th>Display rank</th><th>Reads</th><th>Exact support in B</th></tr>'+rows+'</table><p>Full data: primary_candidates.tsv, corroboration.json, bcr_abl1_trace.json; per-library decisions and freezes.</p>')
    return stats
