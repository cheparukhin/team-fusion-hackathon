#!/usr/bin/env bash
set -euo pipefail
mkdir -p outputs
exec >outputs/setup.log 2>&1
date -u +%FT%TZ
nvidia-smi
if ! python3 -m venv .venv; then
    sudo -n apt-get update
    sudo -n apt-get install -y python3-venv
    python3 -m venv .venv
fi
if ! python3 -c 'import pathlib,sysconfig; assert (pathlib.Path(sysconfig.get_path("include"))/"Python.h").is_file()'; then
    sudo -n apt-get update
    sudo -n apt-get install -y python3-dev build-essential
fi
.venv/bin/python -m pip install --disable-pip-version-check torch==2.6.0+cu126 --index-url https://download.pytorch.org/whl/cu126
echo 'b8c62bbdede1922931d9203118f62c858f11aa699bf91fd4c05a5ed6a6d8b4fc  inputs/boltz-2.2.1-py3-none-any.whl' | sha256sum -c -
.venv/bin/python -m pip install --disable-pip-version-check 'inputs/boltz-2.2.1-py3-none-any.whl[cuda]' \
    torch==2.6.0+cu126 cuequivariance==0.5.0 cuequivariance-torch==0.5.0 cuequivariance-ops-cu12==0.5.0 cuequivariance-ops-torch-cu12==0.5.0
.venv/bin/python -m pip freeze > outputs/requirements-lock.txt
.venv/bin/boltz predict --help > outputs/boltz-predict-help.txt
.venv/bin/python - <<'PY'
import torch
import json
from pathlib import Path
from cuequivariance_torch.primitives.triangle import triangle_multiplicative_update
from boltz.model.layers.triangular_mult import TriangleMultiplicationOutgoing
assert torch.cuda.is_available() and torch.cuda.device_count()==1
assert 'A100' in torch.cuda.get_device_name(0)
assert torch.cuda.get_device_properties(0).total_memory >= 75*1024**3
with torch.inference_mode(), torch.autocast('cuda',dtype=torch.bfloat16):
    module=TriangleMultiplicationOutgoing().cuda().eval()
    torch.nn.init.normal_(module.p_out.weight,std=.02)
    x=torch.randn(1,16,16,128,device='cuda',dtype=torch.bfloat16)
    mask=torch.ones(1,16,16,device='cuda')
    result=module(x,mask,use_kernels=True)
    torch.cuda.synchronize()
    assert result.shape==x.shape and torch.isfinite(result).all()
Path('outputs/cuda-kernel-check.json').write_text(json.dumps({'status':'passed','check':'Boltz triangle multiplication with cuEquivariance kernels on a random 16x16x128 tensor','biological_prediction':False,'torch':torch.__version__,'cuda':torch.version.cuda},indent=2)+'\n')
print(torch.__version__,torch.version.cuda,torch.cuda.get_device_name(0))
PY
date -u +%FT%TZ
