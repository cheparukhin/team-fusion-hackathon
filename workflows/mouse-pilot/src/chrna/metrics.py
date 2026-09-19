from __future__ import annotations

import numpy as np
from scipy.stats import hypergeom


def tie_aware_topk(labels, scores, k: int) -> dict:
    """Expected known-positive recovery under uniform random tie breaking.

    The interval represents tie-breaking variability only, not a confidence
    interval for biological precision. An unconfirmed row is never a true negative.
    """
    raw_labels = np.asarray(labels)
    if (raw_labels.ndim != 1 or raw_labels.dtype.kind not in "biuf"
            or not np.isfinite(raw_labels).all() or not np.isin(raw_labels, [0, 1]).all()):
        raise ValueError("Labels must be non-missing Boolean or numeric binary values")
    y, s = raw_labels.astype(bool), np.asarray(scores, dtype=float)
    if s.ndim != 1 or len(y) != len(s) or len(y) == 0 or not np.isfinite(s).all():
        raise ValueError("Non-empty equal-length labels and finite scores required")
    if k < 1 or k > len(y):
        raise ValueError("k must be between 1 and candidate count")
    threshold = np.sort(s)[-k]
    above, tied = s > threshold, s == threshold
    fixed, remaining = int(y[above].sum()), int(k - above.sum())
    tie_n, tie_p = int(tied.sum()), int(y[tied].sum())
    expected = fixed + remaining * tie_p / tie_n
    lower, upper = hypergeom.ppf([0.025, 0.975], tie_n, tie_p, remaining)
    total_p = int(y.sum())
    return {
        "k": int(k), "candidates": int(len(y)), "known_positives": total_p,
        "expected_supported_at_k": float(expected),
        "known_positive_recall_at_k": float(expected / total_p) if total_p else None,
        "tie_breaking_lower_95": float(fixed + lower),
        "tie_breaking_upper_95": float(fixed + upper),
        "threshold_tie_candidates": tie_n,
        "interval_meaning": "95% variability from random tie-breaking; not biological confidence",
    }
