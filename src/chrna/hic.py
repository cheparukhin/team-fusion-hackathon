"""Candidate-indexed, KR-balanced Hi-C enrichment; no assay labels are inputs."""
from __future__ import annotations
import math
import numpy as np

RESOLUTION = 500_000
WINDOW_BINS = 11

def coordinate_bin(position: int, resolution: int = RESOLUTION) -> int:
    """Map a positive 1-based genomic base to a zero-based bin index."""
    if not isinstance(position, (int, np.integer)) or position < 1:
        raise ValueError('position must be a positive integer (1-based)')
    return (int(position) - 1) // resolution


def genova_enrichment(window: np.ndarray) -> tuple[float, float, float, str]:
    """GENOVA quantify.APA defaults: center3x3/quadrant medians in11x11.

    Sparse *observed* zeros remain zero. Missing normalization or incomplete
    windows remain unavailable. Outlier clipping in GENOVA only affects the
    aggregate plot, not the per-loop raw array used by quantify.
    """
    a = np.asarray(window, dtype=float)
    if a.shape != (WINDOW_BINS, WINDOW_BINS):
        raise ValueError('expected an 11x11 window')
    if not np.isfinite(a).all() or np.any(a < 0):
        return math.nan, math.nan, math.nan, 'unavailable_pixels'
    foreground = float(np.median(a[4:7, 4:7]))
    idx = np.r_[0:4, 7:11]
    background = float(np.median(a[np.ix_(idx, idx)]))
    if background <= 0:
        return foreground, background, math.nan, 'undefined_background'
    return foreground, background, foreground/background, 'observed'


def extract_window(matrix: np.ndarray, bin1: int, bin2: int) -> np.ndarray | None:
    """Reject chromosome-edge windows, as GENOVA anchors_finish does."""
    if bin1 < 5 or bin2 < 5 or bin1 + 5 >= matrix.shape[0] or bin2 + 5 >= matrix.shape[1]:
        return None
    return matrix[bin1-5:bin1+6, bin2-5:bin2+6]


def aggregate_bin_pair_features(rows: list[dict], pair_ids: list[str], expected_replicates: int = 3) -> list[dict]:
    """Average distinct bin-pair ratios within replicate, then replicates.

    A primary feature requires all expected replicates. Partial coverage is
    retained explicitly as a sensitivity feature. No label enters this path.
    """
    output=[]
    for pair in pair_ids:
        subset=[r for r in rows if r['pair_id']==pair]
        groups={}
        for r in subset:
            key=(r['replicate'],r['chrom1'],r['bin1'],r['chrom2'],r['bin2'])
            if math.isfinite(float(r['enrichment'])):
                groups[key]=float(r['enrichment'])
        reps={k[0] for k in groups}
        means=[float(np.mean([v for k,v in groups.items() if k[0]==rep])) for rep in sorted(reps)]
        partial=float(np.mean(means)) if means else math.nan
        primary=partial if len(reps)==expected_replicates else math.nan
        output.append({'pair_id':pair,'hic_contact_enrichment':primary,
                       'hic_feature':math.log2(.5+primary) if math.isfinite(primary) else math.nan,
                       'hic_n_replicates':len(reps),'hic_n_bin_pairs':len({k[1:] for k in groups}),
                       'hic_partial_enrichment':partial,
                       'hic_status':'observed_all_replicates' if len(reps)==expected_replicates else 'incomplete_replicates' if reps else 'unavailable',
                       'hic_qc_reasons':';'.join(sorted({r['status'] for r in subset if r['status']!='observed'})) if subset else 'no_probe_coordinates',
                       'hic_assembly':'GRCm39','hic_resolution':RESOLUTION})
    return output


def mask_invalid_normalization(matrix: np.ndarray, norm1: np.ndarray, norm2: np.ndarray) -> np.ndarray:
    """Distinguish absent KR normalization bins from sparse observed zeros.

    hic-straw drops nonfinite normalized records. Inspect both explicit KR
    vectors (queried with actual chromosome indexes), never infer availability
    solely from records. A short vector masks its unavailable suffix; a missing vector masks the whole axis.
    """
    out=np.array(matrix,dtype=float,copy=True)
    for axis,norm in enumerate((norm1,norm2)):
        valid=np.zeros(out.shape[axis],dtype=bool)
        n=min(len(norm),len(valid))
        valid[:n]=np.isfinite(norm[:n]) & (norm[:n]>0)
        if axis==0:out[~valid,:]=np.nan
        else:out[:,~valid]=np.nan
    return out
