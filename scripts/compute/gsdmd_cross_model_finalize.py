#!/usr/bin/env python3
"""Freeze execution/cost provenance after model and checkpoint verification."""
import argparse,datetime,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root
idx=json.loads((root/'model_index.json').read_text());assert all(m['status']=='verified'for m in idx['models']);checks=json.loads((root/'post_run_integrity.json').read_text());assert checks['checkpoint_unchanged_after_shared_mmap_inference']and checks['prior_ledger_unchanged']
r={'status':'completed_local_cpu','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sequence_sha256':idx['sequence_sha256'],'length_aa':118,'new_distinct_engine_families':['AlphaFold2','ESMFold'],'model_index':str(root/'model_index.json'),'model_index_sha256':hashlib.sha256((root/'model_index.json').read_bytes()).hexdigest(),'new_cloud_allocation_usd':0,'gpu_resume_count':0,'instances_created':0,'external_sequence_uploads':0,'owned_gpu_id':'8mq2074bp','owned_gpu_action':'none; remained stopped; no lifecycle mutation','shared_budget_note':'No new allocation. setup/budget_audit.json is a conservative reservation audit, not a provider invoice; proposed GPU budget increase was unnecessary. Existing controller/background/storage costs are not isolated incremental invoices.','models':[{'engine':m['engine'],'protocol_id':m['protocol_id'],'status':m['status'],'mean_plddt':m['mean_plddt'],'wall_seconds':m['wall_seconds']}for m in idx['models']],'integrity':checks,'script_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(Path('scripts/compute').glob('gsdmd_cross_model_*.py'))},'limitations':['Reference-assisted ORF, not experimentally solved candidate protein.','Different MSA inputs mean architecture effects are not isolated.','One prespecified seed/model per engine; no model selected by highest confidence.','No speedup benchmark claimed; CPU timings include different implementation/setup overhead.']}
r['final_owned_instance_check'] = json.loads((root/'setup/final_inventory_check.json').read_text()) if (root/'setup/final_inventory_check.json').exists() else None
(root/'execution_receipt.json').write_text(json.dumps(r,indent=2)+'\n')
(root/'STATUS.md').write_text('''# Completed local cross-engine comparison

Both new engine families completed on the existing CPU controller. The exact118-aa sequence and every ordered CA residue were verified, with finite118×118 PAE and per-residue confidence exported on0–100.

- AlphaFold2 model1_ptm: mean pLDDT65.5047; total CPU553.4s; selected prediction log482.8s; peak process-tree RSS2.89GB. Cached913-row MSA, capped128:256; no new MSA request.
- ESMFoldv1: mean pLDDT47.1926; inference218.2s; total219.3s (supervisor226.1s). Shared file-backed checkpoint, full float32. Minimum host available memory5.43GB; no guard triggered. Post-run checkpoint SHA unchanged.
- Coordinates, confidence TSVs, PAE and correctly framed blue/red cartoons are linked in model_index.json.
- No GPU restart, new instance, hosted inference call, sequence upload or new cloud allocation. GPU8mq2074bp remained stopped.
- Prior67-model jobs ledger SHA is unchanged. All derived outputs remain inside this cross-model compute directory. Bulk public weights/environments are excluded from Git.

Final model_index SHA256: `'''+r['model_index_sha256']+'''`.

Methods, pinned metadata/software, preserved setup failures and execution_receipt.json provide reproducibility. Confidence is not measured disorder, translation or function. Reference-assisted protein sequence remains a conditional hypothesis.
''')
print(json.dumps({'status':r['status'],'new_cloud_allocation_usd':0,'model_index_sha256':r['model_index_sha256']}))
