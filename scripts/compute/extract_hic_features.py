"""Rebuild candidate Hi-C features from cached public processed .hic files."""
import hashlib,json,math,pathlib,sys
import hicstraw
import numpy as np
import pandas as pd
from chrna.hic import coordinate_bin,genova_enrichment,extract_window,aggregate_bin_pair_features,mask_invalid_normalization,RESOLUTION
ROOT=pathlib.Path(__file__).resolve().parents[2]
out=ROOT/'results/hic'
probes=pd.read_csv(ROOT/'results/dataset_reconstruction/probe_junctions.tsv',sep='\t')
assert set(probes.assembly)=={'GRCm39'}
probes['bin1']=probes.breakpoint1.map(coordinate_bin);probes['bin2']=probes.breakpoint2.map(coordinate_bin)
probes=probes.drop_duplicates(['pair_id','chrom1','bin1','chrom2','bin2'])
man=json.loads((out/'download_manifest.json').read_text());rows=[]
for sample in man:
    path=pathlib.Path(sample['path'])
    if path.stat().st_size!=sample['bytes'] or hashlib.file_digest(path.open('rb'),'sha256').hexdigest()!=sample['sha256']:
        raise ValueError(f"Cached Hi-C input failed size/SHA256 validation: {path}")
for sample in man:
    h=hicstraw.HiCFile(sample['path']);chroms={c.name:(c.index,c.length) for c in h.getChromosomes()}
    cache={}
    for p in probes.itertuples():
        status='observed';fg=bg=ratio=math.nan
        if p.chrom1 not in chroms or p.chrom2 not in chroms:status='chromosome_unavailable'
        elif p.chrom1==p.chrom2 and abs(p.bin1-p.bin2)<1:status='cis_below_500kb_bin_distance'
        else:
            c1,c2=sorted([p.chrom1,p.chrom2],key=lambda c:chroms[c][0]);key=(c1,c2)
            if key not in cache:
                shape=(chroms[c1][1]//RESOLUTION+1,chroms[c2][1]//RESOLUTION+1)
                matrix=np.zeros(shape)
                records=hicstraw.straw('observed','KR',sample['path'],c1,c2,'BP',RESOLUTION)
                for r in records:
                    i,j=r.binX//RESOLUTION,r.binY//RESOLUTION;matrix[i,j]=r.counts
                    if c1==c2:matrix[j,i]=r.counts
                zoom=h.getMatrixZoomData(c1,c2,'observed','KR','BP',RESOLUTION)
                norm1=np.asarray(zoom.getNormVector(chroms[c1][0]))
                norm2=np.asarray(zoom.getNormVector(chroms[c2][0]))
                matrix=mask_invalid_normalization(matrix,norm1,norm2)
                cache[key]=matrix if records else None
            matrix=cache[key]
            if matrix is None:status='KR_matrix_unavailable'
            else:
                b1,b2=(p.bin1,p.bin2) if c1==p.chrom1 else (p.bin2,p.bin1)
                window=extract_window(matrix,b1,b2)
                if window is None:status='chromosome_edge'
                else:fg,bg,ratio,status=genova_enrichment(window)
        rows.append(dict(pair_id=p.pair_id,replicate=sample['replicate'],accession=sample['accession'],chrom1=p.chrom1,bin1=p.bin1,chrom2=p.chrom2,bin2=p.bin2,foreground=fg,background=bg,enrichment=ratio,status=status))
    print(sample['accession'],'complete',len(cache),'matrices',flush=True)
pd.DataFrame(rows).to_csv(out/'bin_pair_contacts.tsv',sep='\t',index=False)
ids=sorted(pd.read_csv(ROOT/'results/dataset_reconstruction/candidates.tsv',sep='\t').pair_id.unique())
features=pd.DataFrame(aggregate_bin_pair_features(rows,ids));features.to_csv(out/'features.tsv',sep='\t',index=False)
meta=dict(status='completed',assembly='GRCm39',resolution_bp=RESOLUTION,normalization='KR (GENOVA balancing=TRUE for Juicer .hic)',window_bins=11,foreground='median central3x3',background='median64 pixels in four4x4 corner quadrants; central rows/columns excluded',transform='log2(0.5+enrichment)',aggregation='mean over distinct ordered probe bin pairs within replicate; equal-weight mean across observed replicates; primary requires all3',paper_deviation='Paper describes merged replicates before processing. GEO supplies individual processed replicate .hic files. This pilot averages independently KR-normalized per-replicate ratios and is not an exact merged-matrix reproduction.',missing='Zero background, absent KR matrix, incomplete edge windows, windows intersecting nonfinite/nonpositive KR normalization bins, unmapped probes, and cis bin distance<500kb remain unavailable; no zero imputation.',feature_counts=features.hic_status.value_counts().to_dict(),genova_sources=['https://github.com/robinweide/GENOVA/blob/master/R/methods_quantify.R','https://github.com/robinweide/GENOVA/blob/master/R/ARMLA.R','https://github.com/robinweide/GENOVA/blob/master/R/loading_juicer.R'],timing='Hi-C LPS6h vs RNA different inflammatory treatment/time; all predictor contacts from siNeg LPS, no CTCF knockdown.',input_probe_sha256=hashlib.file_digest((ROOT/'results/dataset_reconstruction/probe_junctions.tsv').open('rb'),'sha256').hexdigest(),inputs=man)
meta['genova_source_sha256']={p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in out.glob('*.R')}
(out/'feature_manifest.json').write_text(json.dumps(meta,indent=2));print(features.hic_status.value_counts().to_string())
