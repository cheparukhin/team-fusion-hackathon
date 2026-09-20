# chRNA hackathon coordination

Read GAPS.md and STATUS.md before implementation. The coordinator owns shared contracts, root dependencies, src/chrna/model.py, tests/test_model.py, README.md, and final integration.

Worker ownership:
- Data worker: src/chrna/data.py, tests/test_data.py, results/dataset_reconstruction/, data/raw/, data/reference/.
- Compute worker: scripts/compute/, src/chrna/hic.py, tests/test_hic.py, results/compute/, results/hic/.
- Demo worker: demo/, scripts/demo/, results/demo/, tests/test_demo.py.
- Existing animation/ is being developed separately; read/reuse it but do not modify it.

Do not spawn additional agents. Coordinate interface changes with the coordinator. Do not modify another worker's files or root dependency configuration. Work in the shared checkout with the above ownership; no concurrent Git index mutations. Coordinator owns commits.

Scientific invariants: NanoString reported support is the label, not proof that other candidates are false. Preserve ordered pairs, genomic assembly, exact junctions, read IDs, assay missing/QC status, and provenance. Never fabricate missing data or successful results. No shared parent genes across evaluation folds. Model preprocessing must be fitted on training folds only. No validation-derived model inputs. Report unavailable features and unsuccessful technology integrations honestly.

Use real cached artifacts for the final demo and provide commands and focused tests. Save worker-specific status in results/<owned area>/STATUS.md; send concise progress and concrete interface details to the coordinator. Do not expose credentials in logs.

Compute budget: inspect existing Brev instances before creating any. The user's current ceiling is $400/hour across compute; prefer the existing shared CPU and account for concurrent team resources. Do not provision unless a live quote, runtime limit, and compatible hardware are established; retain a spending/runtime record. Prefer existing usable hardware. Do not stop/delete user instances you did not create.
