from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import tie_aware_topk


def benchmark(root: Path, partition: str = "development", evaluate_heldout: bool = False) -> pd.DataFrame:
    if partition == "heldout" and not evaluate_heldout:
        raise ValueError("Freeze the method first; pass --evaluate-heldout to run the reserved partition")
    inputs = pd.read_csv(root / "data/processed/candidate_pairs.csv")
    outcomes = pd.read_csv(root / "data/processed/evaluation_outcomes.csv")
    pool = inputs.loc[inputs.baseline_eligible & (inputs.partition == partition)].copy()
    pool = pool.merge(outcomes[["pair_id", "nanostring_reported_support"]], on="pair_id", validate="one_to_one")
    if len(pool) < 1:
        raise ValueError("Empty evaluation pool")
    scores = {
        "Random selection": np.zeros(len(pool)),
        "Long-read support": pool.long_read_support.to_numpy(),
        "Reported short-read support": pool.short_read_reported_support.astype(int).to_numpy(),
    }
    rows = []
    for name, values in scores.items():
        for k in [10, 20, 50]:
            if k <= len(pool):
                rows.append(dict(method=name, partition=partition,
                                 **tie_aware_topk(pool.nanostring_reported_support, values, k)))
    results = pd.DataFrame(rows)
    results.to_csv(root / f"reports/baselines_{partition}.csv", index=False)
    curves = []
    for name, values in scores.items():
        for k in range(1, min(100, len(pool)) + 1):
            curves.append(dict(method=name, **tie_aware_topk(pool.nanostring_reported_support, values, k)))
    pd.DataFrame(curves).to_csv(root / f"reports/recovery_curves_{partition}.csv", index=False)
    (root / f"reports/benchmark_{partition}.json").write_text(json.dumps({
        "partition": partition, "candidate_count": len(pool),
        "known_positive_count": int(pool.nanostring_reported_support.sum()),
        "methods": list(scores), "scoring_uses_nanostring_outcome": False,
        "candidate_grain": "ordered gene pair", "split": "parent-gene-connected components; fold 4 reserved",
        "endpoint": "recovery of reported NanoString-supported pairs in an author-selected panel",
        "tie_policy": "analytical expectation over uniformly random ties",
        "biological_precision_or_fdr_estimated": False,
        "results": results.replace({np.nan: None}).to_dict("records")
    }, indent=2) + "\n")
    return results


def plot(root: Path, partition: str = "development") -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    data = pd.read_csv(root / f"reports/recovery_curves_{partition}.csv")
    palette = {"Random selection": "#555D66", "Long-read support": "#2456A6", "Reported short-read support": "#A76519"}
    fig, ax = plt.subplots(figsize=(9, 5.4), layout="constrained")
    for name, group in data.groupby("method", sort=False):
        ax.plot(group.k, group.expected_supported_at_k, label=name, color=palette[name],
                linestyle="--" if name == "Random selection" else "-", linewidth=2)
    ax.set(xlabel="Candidates selected (review budget)", ylabel="Reported supported pairs recovered (expected count)",
           title=f"Published RNA support recovery — {partition} partition", xlim=(0, data.k.max()), ylim=(0, None))
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    n, p = int(data.candidates.iloc[0]), int(data.known_positives.iloc[0])
    fig.supxlabel(f"{n} eligible gene pairs; {p} reported NanoString-supported. Ties averaged analytically.\n"
                  "Unconfirmed candidates are not biological negatives. Source: study supplementary tables 3, 7, 8.", fontsize=9)
    path = root / f"reports/recovery_{partition}.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
