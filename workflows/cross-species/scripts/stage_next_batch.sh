#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/cross-species
for run in SRR31438988 SRR31438989 SRR31438990 SRR31429687; do
  python3 -c 'import shutil; assert shutil.disk_usage(".").free > 35*1024**3, "Insufficient free scratch disk"'
  software/bin/micromamba run -p software/env python scripts/fetch_inputs.py --run "$run"
done
