#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/cross-species
export MAMBA_ROOT_PREFIX="$PWD/software/mamba"
for species in homo_sapiens bos_taurus; do
  while [ ! -f "reference/$species/adapted/adapter_qc.json" ]; do sleep 15; done
  software/bin/micromamba run -p "$PWD/software/env" python scripts/prepare_jaffal_reference.py "$species" > "logs/jaffal_reference_$species.log" 2>&1
done
