#!/usr/bin/env python3
"""Validate existing pinned environment and model cache after an owned-host resume."""
import argparse,hashlib,json,sys,importlib.metadata,sysconfig
from pathlib import Path
import torch
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--weights-manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert importlib.metadata.version('boltz')=='2.2.1'
assert torch.__version__=='2.6.0+cu126'
assert (Path(sysconfig.get_path('include'))/'Python.h').is_file()
assert torch.cuda.is_available()and torch.cuda.device_count()==1
assert 'A100'in torch.cuda.get_device_name(0)and torch.cuda.get_device_properties(0).total_memory>=75*1024**3
from boltz.model.layers.triangular_mult import TriangleMultiplicationOutgoing
with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
 module=TriangleMultiplicationOutgoing().cuda().eval();torch.nn.init.normal_(module.p_out.weight,std=.02)
 x=torch.randn(1,16,16,128,device='cuda',dtype=torch.bfloat16);mask=torch.ones(1,16,16,device='cuda');result=module(x,mask,use_kernels=True);torch.cuda.synchronize();assert result.shape==x.shape and torch.isfinite(result).all()
files=[]
for r in json.loads(a.weights_manifest.read_text())['files']:
 file=a.cache/r['rfilename'];assert file.stat().st_size==r['size'];h=hashlib.sha256()
 with file.open('rb')as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 assert h.hexdigest()==r['lfs']['sha256'];files.append({'name':file.name,'sha256':h.hexdigest(),'bytes':file.stat().st_size})
assert (a.cache/'mols').is_dir()
a.output.write_text(json.dumps({'status':'passed','python':sys.version,'boltz':'2.2.1','torch':torch.__version__,'gpu':torch.cuda.get_device_name(0),'kernel_test':'finite_triangle_update','weight_files':files},indent=2)+'\n')
print('Existing pinned environment, CUDA primitive and model cache verified')
