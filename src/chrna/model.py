"""Retrospective reported-support prediction with parent-gene-disjoint evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
RNA_FEATURES = ["log_read_support", "sample_count", "is_interchromosomal", "log_genomic_distance"]
LIMITATIONS = [
    "The target is published NanoString support within a selected probe-design panel, not biological authenticity.",
    "Unreported support is not a verified negative; testing and probe QC may be unknown.",
    "Labels and predictions refer to ordered parent-gene pairs, not validated junction isoforms.",
    "Out-of-fold scores are not calibrated probabilities; all-data refit scores are not evaluation results.",
    "The selected panel and parent-gene grouping limit generalization to unseen tissues and datasets.",
    "Bootstrap intervals resample parent-gene components of fixed out-of-fold predictions; they do not capture model-refitting uncertainty.",
]


def gene_components(frame: pd.DataFrame) -> np.ndarray:
    """All pairs sharing either parent, including transitive links, remain together."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in zip(frame.parent_a, frame.parent_b):
        ra, rb = find(str(a)), find(str(b))
        parent[max(ra, rb)] = min(ra, rb)
    return np.array([find(str(a)) for a in frame.parent_a])


def validate(frame: pd.DataFrame) -> pd.DataFrame:
    needed = {"pair_id", "parent_a", "parent_b", "label", "long_read_support", "sample_count",
              "is_interchromosomal", "genomic_distance"}
    missing = needed - set(frame)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    frame = frame.copy().sort_values("pair_id").reset_index(drop=True)
    if frame.pair_id.isna().any() or frame.pair_id.duplicated().any():
        raise ValueError("Pair IDs must be nonmissing and unique")
    if frame[["parent_a", "parent_b"]].isna().any().any():
        raise ValueError("Both parent identifiers are required")
    for col in ["label", "long_read_support", "sample_count", "is_interchromosomal", "genomic_distance"]:
        frame[col] = pd.to_numeric(frame[col], errors="raise")
        if np.isinf(frame[col]).any():
            raise ValueError(f"Infinite {col}")
    if frame.label.isna().any() or not set(frame.label.unique()) <= {0, 1}:
        raise ValueError("Labels must be binary published-support indicators")
    if frame.is_interchromosomal.isna().any() or not set(frame.is_interchromosomal.unique()) <= {0, 1}:
        raise ValueError("Chromosome relationship must be known and binary")
    for col in ["long_read_support", "sample_count", "genomic_distance"]:
        if (frame[col].dropna() < 0).any():
            raise ValueError(f"Negative {col}")
    return frame


def feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["log_read_support"] = np.log1p(frame.long_read_support)
    out["sample_count"] = frame.sample_count
    out["is_interchromosomal"] = frame.is_interchromosomal
    distance = frame.genomic_distance.where(frame.is_interchromosomal == 0, 0)
    out["log_genomic_distance"] = np.log1p(distance)
    if "hic_contact_enrichment" in frame:
        contact = pd.to_numeric(frame.hic_contact_enrichment, errors="raise")
        if (contact.dropna() < 0).any() or np.isinf(contact).any():
            raise ValueError("Hi-C enrichment must be finite nonnegative or missing")
        out["hic_feature"] = np.log2(0.5 + contact)
    return out


def estimator():
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=5000, random_state=SEED),
    )


def split_folds(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    groups = gene_components(frame)
    for n in [5, 3]:
        if len(np.unique(groups)) < n or frame.label.value_counts().min() < n:
            continue
        folds = np.full(len(frame), -1, dtype=int)
        splitter = StratifiedGroupKFold(n_splits=n, shuffle=True, random_state=SEED)
        valid = True
        for fold, (train, test) in enumerate(splitter.split(frame, frame.label, groups)):
            if frame.iloc[train].label.nunique() < 2 or frame.iloc[test].label.nunique() < 2:
                valid = False
                break
            train_genes = set(frame.iloc[train].parent_a) | set(frame.iloc[train].parent_b)
            test_genes = set(frame.iloc[test].parent_a) | set(frame.iloc[test].parent_b)
            if train_genes & test_genes:
                raise AssertionError("Parent-gene leakage detected")
            folds[test] = fold
        if valid and (folds >= 0).all():
            return folds, groups
    raise ValueError("Cannot form three gene-disjoint folds containing both labels; do not use a random split")


def evaluate(y, scores, ids, k=20) -> dict:
    y, scores, ids = np.asarray(y, dtype=int), np.asarray(scores, dtype=float), np.asarray(ids, dtype=str)
    valid = np.isfinite(scores)
    y, scores, ids = y[valid], scores[valid], ids[valid]
    if not len(y):
        return {"n": 0, "status": "unavailable"}
    top = np.lexsort((ids, -scores))[:k]
    positives = int(y.sum())
    return {
        "n": len(y), "positives": positives, "prevalence": float(y.mean()),
        "average_precision": float(average_precision_score(y, scores)) if positives and positives < len(y) else None,
        "k": len(top), "supported_at_k": int(y[top].sum()),
        "precision_at_k": float(y[top].mean()),
        "recall_at_k": float(y[top].sum() / positives) if positives else None,
    }


def bootstrap_difference(y, score_a, score_b, groups, n=1000) -> dict:
    y, a, b, groups = map(np.asarray, (y, score_a, score_b, groups))
    unique = np.unique(groups)
    indices = {g: np.flatnonzero(groups == g) for g in unique}
    rng, differences = np.random.default_rng(SEED), []
    for _ in range(n):
        ix = np.concatenate([indices[g] for g in rng.choice(unique, len(unique), replace=True)])
        if np.unique(y[ix]).size == 2:
            differences.append(average_precision_score(y[ix], b[ix]) - average_precision_score(y[ix], a[ix]))
    point = average_precision_score(y, b) - average_precision_score(y, a)
    return {"delta_average_precision": float(point), "ci95": np.quantile(differences, [.025, .975]).tolist() if differences else None,
            "valid_resamples": len(differences), "requested_resamples": n, "seed": SEED,
            "method": "parent_gene_component_bootstrap_of_fixed_oof_predictions"}


def run(input_path: Path, output: Path, hic_path: Path | None = None, bootstrap_n: int = 1000) -> dict:
    frame = validate(pd.read_csv(input_path, sep="\t"))
    hic_provenance = None
    if hic_path:
        manifest_path = hic_path.parent / "feature_manifest.json"
        hic_provenance = {"feature_file": str(hic_path), "feature_sha256": hashlib.sha256(hic_path.read_bytes()).hexdigest(),
                          "feature_manifest": str(manifest_path) if manifest_path.exists() else None,
                          "feature_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path.exists() else None,
                          "method": json.loads(manifest_path.read_text()) if manifest_path.exists() else None}
        hic = pd.read_csv(hic_path, sep="\t")
        if hic.pair_id.duplicated().any():
            raise ValueError("Hi-C feature table must have one row per pair")
        if "hic_contact_enrichment" not in hic:
            raise ValueError("Hi-C table lacks hic_contact_enrichment")
        frame = frame.drop(columns=["hic_contact_enrichment"], errors="ignore").merge(
            hic[["pair_id", "hic_contact_enrichment"]], on="pair_id", how="left", validate="one_to_one")
    folds, groups = split_folds(frame)
    x = feature_frame(frame)
    frame["fold"], frame["group_id"] = folds, groups
    frame["score_rna"] = np.nan
    frame["score_hic"] = np.nan
    frame["score_rna_matched"] = np.nan
    # A ranking rule, never an imputed biological count.
    frame["score_read_support"] = frame.long_read_support.fillna(-1)
    has_hic = "hic_feature" in x and x.hic_feature.notna().any()
    if has_hic:
        has_hic = frame.loc[x.hic_feature.notna(), "label"].nunique() == 2
    model_features = {"rna": RNA_FEATURES}
    if has_hic:
        model_features["rna_matched"] = RNA_FEATURES
        model_features["hic"] = RNA_FEATURES + ["hic_feature"]
    output.mkdir(parents=True, exist_ok=True)
    for name, cols in model_features.items():
        cohort = np.ones(len(frame), dtype=bool) if name == "rna" else x.hic_feature.notna().to_numpy()
        for fold in sorted(set(folds)):
            train, test = (folds != fold) & cohort, (folds == fold) & cohort
            if frame.loc[train, "label"].nunique() < 2:
                raise ValueError(f"Matched training cohort lacks both labels in fold {fold}")
            model = estimator().fit(x.loc[train, cols], frame.loc[train, "label"])
            if test.any():
                frame.loc[test, f"score_{name}"] = model.predict_proba(x.loc[test, cols])[:, 1]
        refit = estimator().fit(x.loc[cohort, cols], frame.loc[cohort, "label"])
        joblib.dump({"model": refit, "features": cols, "target": "reported_NanoString_support", "seed": SEED}, output / f"model_{name}.joblib")
    metrics = {
        "status": "complete", "target": "reported_NanoString_support_in_probe_panel", "seed": SEED,
        "hic_provenance": hic_provenance,
        "model_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cohort": {"n": len(frame), "positives": int(frame.label.sum()), "groups": len(set(groups)),
                   "folds": len(set(folds)), "largest_group": int(pd.Series(groups).value_counts().max()),
                   "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest()},
        "features": {"rna": RNA_FEATURES, "hic": RNA_FEATURES + ["hic_feature"] if has_hic else None,
                     "missing_fraction": {c: float(x[c].isna().mean()) for c in x}},
        "full_panel": {}, "matched_hic": None, "interchromosomal": {}, "limitations": LIMITATIONS.copy(),
    }
    for name, col in [("read_support", "score_read_support"), ("rna", "score_rna")]:
        metrics["full_panel"][name] = evaluate(frame.label, frame[col], frame.pair_id)
        sub = frame[frame.is_interchromosomal == 1]
        metrics["interchromosomal"][name] = evaluate(sub.label, sub[col], sub.pair_id)
    metrics["rna_vs_read_support"] = bootstrap_difference(frame.label, frame.score_read_support, frame.score_rna, frame.group_id, bootstrap_n)
    common = frame.long_read_support.notna()
    metrics["observed_read_support"] = {name: evaluate(frame.loc[common, "label"], frame.loc[common, col], frame.loc[common, "pair_id"])
                                        for name, col in [("read_support", "score_read_support"), ("rna", "score_rna")]}
    if not common.all():
        metrics["limitations"].append("The read-support baseline ranks unavailable counts last, tied by pair ID; missing counts are not interpreted as zero. An observed-support sensitivity analysis is also reported.")
    if has_hic:
        sub = frame.loc[x.hic_feature.notna()]
        metrics["matched_hic"] = {name: evaluate(sub.label, sub[col], sub.pair_id) for name, col in
                                  [("read_support", "score_read_support"), ("rna", "score_rna_matched"), ("hic", "score_hic")]}
        metrics["matched_hic"]["comparison"] = bootstrap_difference(sub.label, sub.score_rna_matched, sub.score_hic, sub.group_id, bootstrap_n)
        trans = sub[sub.is_interchromosomal == 1]
        metrics["matched_hic"]["interchromosomal"] = {name: evaluate(trans.label, trans[col], trans.pair_id) for name, col in [("rna", "score_rna_matched"), ("hic", "score_hic")]}
        metrics["matched_hic"]["fold_cohorts"] = [
            {"fold": int(f), "train_n": int((sub.fold != f).sum()), "train_positives": int(sub.loc[sub.fold != f, "label"].sum()),
             "test_n": int((sub.fold == f).sum()), "test_positives": int(sub.loc[sub.fold == f, "label"].sum())}
            for f in sorted(set(folds))]
        metrics["matched_hic"]["training_policy"] = "Both RNA and RNA+Hi-C are trained on identical complete-contact training rows within the fixed gene-disjoint folds; no contact-availability feature is used."
        # RNA-only is the published score when contact context is unavailable.
        frame.loc[x.hic_feature.isna(), "score_hic"] = np.nan
        metrics["limitations"].append("Hi-C is regional 500-kb context, not splice-junction resolution; its assay timing differs from RNA measurements.")
    else:
        metrics["limitations"].append("Candidate-indexed Hi-C features with both target classes were not available; the spatial hypothesis was not tested.")
    if x.sample_count.isna().all():
        metrics["limitations"].append("Public long-read tables do not supply sample-level read provenance; recurrence is unavailable and contributes no signal.")
    frame.to_csv(output / "predictions.tsv", sep="\t", index=False)
    pd.concat([frame[["pair_id"]], x], axis=1).to_csv(output / "features.tsv", sep="\t", index=False)
    frame[["pair_id", "parent_a", "parent_b", "label", "group_id", "fold"]].to_csv(output / "folds.tsv", sep="\t", index=False)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    (output / "MODEL_CARD.md").write_text(model_card(metrics))
    return metrics


def model_card(metrics: dict) -> str:
    lines = ["# chRNA reported-support classifier", "", "Target: published NanoString support within the mapped probe panel.",
             "", "L2 logistic regression, C=1; fold-local median imputation, missingness indicators, and standardization.",
             "Parent-gene connected components are kept entirely within folds; all displayed evaluation scores are out-of-fold.",
             "", "## Evaluation", "", "| Method | N | Average precision | Supported / top 20 |", "|---|---:|---:|---:|"]
    for name, result in metrics["full_panel"].items():
        ap = result.get("average_precision")
        lines.append(f"| {name} | {result['n']} | {ap:.3f} | {result['supported_at_k']} / {result['k']} |" if ap is not None else f"| {name} | {result['n']} | unavailable | |")
    if metrics["matched_hic"]:
        lines += ["", "Hi-C comparison trains and evaluates both models on identical rows with observed contact enrichment, within the original folds; see metrics.json."]
    if metrics.get("hic_provenance") and metrics["hic_provenance"].get("method"):
        method = metrics["hic_provenance"]["method"]
        lines += ["", "Hi-C method: " + str(method.get("aggregation", "See feature manifest.")),
                  "", "Paper deviation: " + str(method.get("paper_deviation", "See feature manifest."))]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in metrics["limitations"]]
    lines += ["", "Saved joblib files are local trusted artifacts for all-data refitting; do not load untrusted pickle/joblib files.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/dataset_reconstruction/model_input.tsv"))
    parser.add_argument("--output", type=Path, default=Path("results/classifier"))
    parser.add_argument("--hic", type=Path)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    metrics = run(args.input, args.output, args.hic, args.bootstrap)
    print(json.dumps({k: metrics[k] for k in ["status", "cohort", "full_panel", "matched_hic"]}, indent=2))


if __name__ == "__main__":
    main()
