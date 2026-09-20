#!/usr/bin/env python3
"""Exact-sequence local ESMFold inference; no hosted inference or MSA requests."""
import argparse
import csv
import hashlib
import json
import mmap
import os
import time
from datetime import datetime, timezone
from pathlib import Path

SHA = 'f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
REVISION = '75a3841ee059df2bf4d56688166c8fb459ddd97a'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--initialize-only', action='store_true')
    a = p.parse_args()
    root = a.root.resolve()
    out = root / f'esmfold_{a.device}'
    out.mkdir(exist_ok=True)
    seq = ''.join(x.strip() for x in (root/'inputs/sequence.fasta').read_text().splitlines() if not x.startswith('>'))
    assert len(seq) == 118 and hashlib.sha256(seq.encode()).hexdigest() == SHA
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import numpy as np
    import torch
    from transformers import EsmConfig, EsmForProteinFolding, AutoTokenizer
    torch.set_num_threads(2)
    torch.manual_seed(20260919)
    started = time.monotonic()
    receipt = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                   sequence_sha256=SHA, length_aa=118, device=a.device,
                   torch_version=torch.__version__, weight_revision=REVISION,
                   seed=20260919, num_recycles=3, chunk_size=32,
                   precision='float32', loading='shared file-backed mmap; meta initialization; assign state dict',
                   external_sequence_uploads=0, sequence_cropped=False)
    def save():
        (out/'run.json').write_text(json.dumps(receipt, indent=2)+'\n')
    save()
    try:
        weights = root/'setup/weights/esmfold_v1'
        # Shared mapping permits reclaimable file-backed pages on a small CPU host.
        # Inference does not mutate any model parameters; checkpoint hash is checked separately.
        torch.serialization.set_default_mmap_options(mmap.MAP_SHARED)
        state = torch.load(weights/'pytorch_model.bin', mmap=True, weights_only=True, map_location='cpu')
        config = EsmConfig.from_pretrained(weights, local_files_only=True)
        with torch.device('meta'):
            model = EsmForProteinFolding(config)
        result = model.load_state_dict(state, strict=False, assign=True)
        receipt['missing_keys'] = result.missing_keys
        receipt['unexpected_keys'] = result.unexpected_keys
        # The folding checkpoint omits the unused ESM contact regression head.
        # Recent Transformers adds this head; folding does not call it.
        assert set(result.missing_keys) == {'esm.contact_head.regression.weight', 'esm.contact_head.regression.bias'}, result.missing_keys
        assert set(result.unexpected_keys) == {'esm.embeddings.position_ids', 'esm.embeddings.position_embeddings.weight'}, result.unexpected_keys
        model.esm.contact_head = None
        receipt['unused_contact_head_removed'] = True
        model.esm.embeddings.position_ids = state['esm.embeddings.position_ids']
        del state
        meta_buffers = [name for name, tensor in model.named_buffers() if tensor.device.type == 'meta']
        assert not meta_buffers, meta_buffers
        model.eval().requires_grad_(False)
        model.trunk.set_chunk_size(32)
        if a.device == 'cuda':
            model = model.cuda()
        receipt['initialization_seconds'] = time.monotonic()-started
        save()
        print('initialized', receipt['initialization_seconds'], flush=True)
        if a.initialize_only:
            receipt['status'] = 'initialized_only'
            save()
            return
        tokenizer = AutoTokenizer.from_pretrained(weights, local_files_only=True)
        inputs = tokenizer(seq, return_tensors='pt', add_special_tokens=False)['input_ids'].to(a.device)
        infer_started = time.monotonic()
        with torch.inference_mode():
            outputs = model(inputs, num_recycles=3)
        if a.device == 'cuda':
            torch.cuda.synchronize()
        receipt['inference_seconds'] = time.monotonic()-infer_started
        cpu_outputs = {k: v.cpu() for k, v in outputs.items()}
        (out/'model.pdb').write_text(model.output_to_pdb(cpu_outputs)[0])
        plddt = cpu_outputs['plddt'][0, :, 1].numpy()
        assert plddt.shape == (118,) and np.isfinite(plddt).all()
        # Transformers categorical_lddt returns confidence on the native 0-1 scale.
        assert float(plddt.min()) >= 0 and float(plddt.max()) <= 1
        plddt100 = plddt * 100
        with (out/'residue_confidence.tsv').open('w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['residue', 'aa', 'plddt'])
            writer.writerows((i+1, aa, float(v)) for i,(aa,v) in enumerate(zip(seq,plddt100)))
        np.savez_compressed(out/'pae.npz', pae=cpu_outputs['predicted_aligned_error'][0].numpy())
        receipt.update(status='process_completed', confidence_native_scale='0-1', confidence_export_scale='0-100',
                       plddt_mean=float(plddt100.mean()), ptm=float(cpu_outputs['ptm'].item()))
    except Exception as e:
        receipt.update(status='failed', error=f'{type(e).__name__}: {e}')
        raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-started, finished_utc=datetime.now(timezone.utc).isoformat())
        save()


if __name__ == '__main__':
    main()
