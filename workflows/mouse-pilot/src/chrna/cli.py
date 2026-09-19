from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import build, fetch
from .benchmark import benchmark, plot


def main():
    parser = argparse.ArgumentParser(description="Chimeric RNA evidence audit and baseline benchmark")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch")
    sub.add_parser("build")
    run = sub.add_parser("benchmark")
    run.add_argument("--partition", choices=["development", "heldout"], default="development")
    run.add_argument("--evaluate-heldout", action="store_true")
    case = sub.add_parser("inspect")
    case.add_argument("pair", help="Ordered gene pair, for example Gsdmd:Tmem106a")
    case.add_argument("--include-published-outcomes", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "fetch":
        fetch(root)
    elif args.command == "build":
        print(json.dumps(build(root), indent=2))
    elif args.command == "benchmark":
        result = benchmark(root, args.partition, args.evaluate_heldout)
        print(result[["method", "k", "expected_supported_at_k", "known_positive_recall_at_k"]].to_string(index=False))
        print(plot(root, args.partition))
    elif args.command == "inspect":
        import pandas as pd
        candidates = pd.read_csv(root / "data/processed/candidate_pairs.csv")
        row = candidates.loc[candidates.pair_id == args.pair]
        if row.empty:
            parser.error("Pair not present in the probe-panel dataset")
        payload = {"features": json.loads(row.to_json(orient="records"))[0],
                   "note": "Pair-level evidence; no individual protein prediction is made."}
        if args.include_published_outcomes:
            outcomes = pd.read_csv(root / "data/processed/evaluation_outcomes.csv")
            payload["published_outcome"] = json.loads(outcomes.loc[outcomes.pair_id == args.pair].to_json(orient="records"))[0]
            payload["benchmark_warning"] = "Published outcomes shown for case review, not ranking input."
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
