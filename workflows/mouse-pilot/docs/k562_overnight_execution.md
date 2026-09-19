# K562 overnight external verification

Owner authorized execution on 2026-09-19, with USD 500 remaining total Brev credits and no disruption of other users. This is a separate human RNA pilot following the completed mouse pilot; the old mouse deadline and SG-NEx deferral do not block this newly authorized run.

## Scope

Two complete SG-NEx K562 Nanopore direct-RNA libraries (replicates 4 and 5), one paired Illumina library (replicate 4), frozen per-library RNA mapping assessment, exact-junction corroboration, and repeated deterministic real-read subset. PacBio, additional cDNA libraries, Hi-C, protein predictions, and training are not included. Biological sample independence remains UNKNOWN.

## Execution and costs

Dedicated n2d-standard-16 CPU worker, 16 vCPU / 64 GiB advertised, 250 GiB disk requested; maximum eight-hour lease. Quoted regional upper rate including disk: USD 1.381882/hour; eight-hour bound USD 11.055056. Incremental allowance USD 20. Expected duration 3–6 hours and cost about USD 3–8; actual billing is not yet known. Live inventory and provider quotes are archived. Existing resources are untouched; the all-visible-resource eight-hour conservative estimate was USD 84.71. This arithmetic is not a provider-enforced spending limit.

A detached controller owns only the new instance ID, validates source hashes, runs the stages, copies outputs and verifies checksums, then stops the instance. Deletion follows only successful preservation. An independent watchdog stops the owned instance at the lease expiry. No credentials or raw sequencing archives are committed.

## Artifacts

[Visual progress and final overview](../runs/k562-pilot/20260919-overnight/progress.html) updates during the run. Detailed scientific report and candidate table are placed under that run's outputs directory after preservation. Machine-readable progress, budget, source-freeze, preservation and shutdown receipts live beside the report.

Validation: 110 tests passed; reproducible data build and development-only benchmark passed. The held-out mouse partition was not evaluated.

Lease cutoff UTC: 2026-09-20T06:40:11.267588+00:00.
