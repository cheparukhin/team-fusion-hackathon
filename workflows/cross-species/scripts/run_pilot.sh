#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/cross-species
while [ ! -f qc/environment_ready ] || [ ! -f qc/pilot_downloads_ready ]; do sleep 15; done
# Repeat against the corrected complete-assembly manifest; existing checksummed files reused.
python3 scripts/download_pilot.py
export MAMBA_ROOT_PREFIX="$PWD/software/mamba"
software/bin/micromamba run -p "$PWD/software/env" python scripts/pilot.py
