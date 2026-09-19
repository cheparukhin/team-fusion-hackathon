"""Check normalized live quotes before provisioning; never provisions anything."""
import argparse
import json
import math
from pathlib import Path


def check(policy, running_rates, proposed_rate):
    rates = list(running_rates) + [proposed_rate]
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x < 0 for x in rates):
        raise ValueError("All project resource rates must be known, finite, non-negative USD/hour values")
    total = sum(rates)
    if total > policy["max_combined_hourly_rate"]:
        raise ValueError(f"Proposed total ${total:.4f}/hour exceeds the project ceiling")
    return {"allowed": True, "combined_usd_per_hour": total,
            "note": "Preflight arithmetic only; verify current rates, resource inventory and actual launch."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=Path("infra/budget-policy.json"))
    parser.add_argument("--running-rates", type=float, nargs="*", default=[])
    parser.add_argument("--proposed-rate", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(check(json.loads(args.policy.read_text()), args.running_rates, args.proposed_rate), indent=2))
