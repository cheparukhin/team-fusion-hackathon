#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/cross-species
export MAMBA_ROOT_PREFIX="$PWD/software/mamba"
mkdir -p software/bin logs
curl -fL --retry 3 https://micro.mamba.pm/api/micromamba/linux-64/latest -o software/micromamba.tar.bz2
python3 -c "import tarfile; t=tarfile.open('software/micromamba.tar.bz2'); t.extract('bin/micromamba', 'software')"
sha256sum software/micromamba.tar.bz2 > software/micromamba.sha256
sed '/  - defaults/d' software/TYPHON/environment.yml > software/environment.yml
cat >> software/environment.yml <<'YAML'

  - gffread
  - pysam
  - sra-tools
  - cxx-compiler
  - cmake
  - make
  - patch
  - git
  - requests
YAML
software/bin/micromamba create -y -p "$PWD/software/env" -f software/environment.yml
software/bin/micromamba list -p "$PWD/software/env" --explicit > software/environment.explicit.txt
touch qc/environment_ready
