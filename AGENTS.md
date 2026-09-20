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

Compute placement: reserve `chrna-controller` for lightweight shared-repository operations only. Run analyses, annotation, indexing, tests, rendering, compression and all other CPU- or memory-heavy work on separate worker instances. Return reviewed results to the shared repository; coordinate commits and avoid concurrent Git index mutations. Bounded thread counts do not make analysis acceptable on the controller.

Before any controller recovery or restart, coordinate with the owner and inspect for stale heavy jobs and the known folding `provision_fallback.py` launcher. Do not resume those workloads on the controller. This policy does not authorize a restart, new provisioning or deadline extension.

Compute budget: inspect existing Brev instances and live rates before creating any. The current shared project ceiling is $200/hour, counting each instance once across tasks; use the headroom only when needed. Prefer existing suitable worker hardware. Require a live quote, compatible hardware, a fixed runtime cutoff and independently enforceable shutdown controls; retain cost/runtime receipts. Do not stop or delete teammate instances you did not create without explicit authorization.
