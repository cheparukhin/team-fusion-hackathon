# Focused pilot execution

Use `/home/ubuntu/workspace/chrna` as the canonical workspace. The compatibility
symlink `/srv/chrna-team/project` remains valid for earlier receipts and running
processes. The current scope and deadlines are in `execution_goal.md`; the
older full-cohort runbook is historical. No held-out benchmark is part of this run.

## Discovery and acceptance

The coordinating task launched `scripts/run_pilot_worker.py` with attempt
directory `runs/focused-pilot-20260919/retry-2`. That controller owns its worker,
input transfer, timeout, retrieval and shutdown. Inspect its live PID and logs
before doing anything with the worker; never launch a second controller while
it is active. Ad hoc Brev/SSH transport requires `SHELL=/bin/sh` for this service
account. Do not alter the account login shell.

After the attempt succeeds and shutdown is confirmed:

```bash
.venv-reproduction/bin/python scripts/accept_pilot_outputs.py \
  --attempt runs/focused-pilot-20260919/retry-2
.venv-reproduction/bin/python scripts/export_split_read_identity.py
.venv-reproduction/bin/snakemake --snakefile workflow/Snakefile --cores 2 pilot_orfs
```

Acceptance checks the full 2,238,871 primary records, BAM completeness, core
output checksums, split-read FASTQ identities and both audit SAM query streams.
It exposes the accepted output directory through a `discovery` symlink without
copying the data again. Snakemake owns resumable assessment and ORF outputs.
The technical controls are in `technical-controls`; they are not biological
pilot results and must never be promoted to the discovery directory.

## Review and freeze

The assessment exports every assigned exact junction, read decision, transcript
competitor and mapping alternative. Unassigned segments and unresolved LongGF
source proposals have separate ledgers. Review those ledgers and any failures
before selection. RNA ranking never receives published outcomes.

```bash
.venv-reproduction/bin/python -m chrna.pilot_selection \
  --assessment runs/focused-pilot-20260919/assessment \
  --orfs runs/focused-pilot-20260919/orfs \
  --output runs/focused-pilot-20260919/selection-preview-1
```

Preview directories and freeze directories cannot be overwritten. Investigate
sequence conflicts, incomplete supporting-read reconstruction and deferrals.
Expand the reconstruction batch beyond 100 only when needed to find enough
defensible sequences, retaining previous receipts. Do not relax rules to rescue
a published example. When the computational method and batch are settled:

```bash
.venv-reproduction/bin/python -m chrna.pilot_selection \
  --assessment runs/focused-pilot-20260919/assessment \
  --orfs runs/focused-pilot-20260919/orfs \
  --output runs/focused-pilot-20260919/selection --freeze
```

The freeze preserves the full RNA ranking, selection rules, sequence hypotheses,
deferrals and hashes. Selection targets eight ranked distinct proteins plus a
singleton and a different junction/ORF-phase class; missing diversity slots are
filled by remaining rank. Global edit distance at most 5% defines folding
redundancy. Reference assistance remains an explicit sequence assumption.

## Separate control and folding

`scripts/prepare_published_control.py` reconstructs the separately labelled
published exon architecture from GENCODE M28 and checks its 118-residue product
against the UniProt parental prefix and the paper's tail/peptide/residue
constraints. This is not de novo recovery and not an author-provided full-sequence
file. The UniProt response, figure, article, reference coordinates and all
reconstruction candidates are preserved. Its cached MSA was prepared using the
hash-verified Boltz 2.2.1 client and the public ColabFold endpoint.

```bash
.venv-reproduction/bin/python -m chrna.fold_inputs \
  --output runs/focused-pilot-20260919/fold-inputs
```

This command requires an unchanged freeze. It deduplicates identical sequences
while retaining separate recovered/control roles. Then run:

```bash
.venv-reproduction/bin/python scripts/prepare_fold_msas.py \
  --inputs runs/focused-pilot-20260919/fold-inputs
```

The batch uses a 900-second per-sequence timeout and a 30-minute batch limit,
reuses verified MSAs and records unavailable sequences as compute deferrals.
The timing pilot takes the shortest, median and longest available sequences;
the frozen protein selection is unchanged. Never silently replace an unavailable
MSA with an empty one. The client dependency added to the controller environment is
`tqdm==4.67.1`; the Boltz wheel and model-file revision/hashes are recorded in
`boltz-preparation`.

`scripts/run_boltz_worker.py --inputs <fold-input-directory>` is a one-attempt
GPU controller. Launch only after available inputs are verified and unavailable
MSAs have explicit deferral records. It checks fresh USD
quotes, all known project resources and attached storage against the budget
utility; unknown resources/prices fail closed. It uses one A100 80-GB worker,
checks hardware, installs the pinned Boltz wheel with its CUDA extras,
Torch 2.6.0/CUDA 12.6 and cuEquivariance 0.5.0,
verifies model hashes, and preserves a full environment lock. It has an
independent watchdog and stops its owned worker after success or failure.

The initial GPU attempt stopped before inference because its 300-GiB all-disk
guard also counted the provider's local NVMe. The observed disks total about
1,142 GiB. The bounded retry prices every visible disk conservatively as
persistent storage up to 1,200 GiB. `--attempt-dir` preserves each lease;
`--resume-from` requires the previous lease's confirmed shutdown and the same
owned instance ID, then reads fresh quotes before restarting it. See
`active-folding-attempt.json` and `gpu-storage-diagnosis.json`; do not issue a
duplicate launch. The actual source bundle hash is recorded for each attempt.
The first inference attempt lacked the CUDA extras and failed all three timing
jobs with a missing cuEquivariance import; production was deferred. The next
environment repair adds the documented extras and imports the required triangle
primitive during setup. CUDA 12.6 satisfies their cuBLAS >=12.5 requirement;
the earlier Torch CUDA 12.4 build pins an incompatible cuBLAS dependency.
The following attempt exposed absent system Python headers during Triton helper
compilation. Setup now ensures `python3-dev`/`build-essential` are present and
executes a small, finite-output Boltz triangle-kernel check before predictions.
This is a technical environment test, not a biological result.

The inference runner starts with shortest, median and longest available
sequences. Standard Boltz-2 settings are three recycling steps, 200 sampling
steps, one sample, step scale 1.5 and a recorded seed. Subsequent jobs require
measured successful timing and enough remaining time. Predictions must match
the input amino-acid sequence exactly and contain finite coordinates, per-residue
pLDDT and a complete PAE matrix. Confidence is not evidence of expression/function.
No repeat or parental inference is scheduled by default.

## Reporting and verification

```bash
.venv-reproduction/bin/python -m chrna.pilot_comparison \
  --output runs/focused-pilot-20260919/published-comparison
.venv-reproduction/bin/python scripts/accept_boltz_outputs.py
.venv-reproduction/bin/python -m chrna.pilot_report
.venv-reproduction/bin/pytest -q
.venv-reproduction/bin/chrna build
.venv-reproduction/bin/chrna benchmark
```

The structure acceptance command runs only after worker outputs are copied. It
rechecks every transferred file hash, amino-acid sequence and confidence array,
then exports coordinate/confidence figures and per-residue CSVs. The HTML
generator remains an explicitly unfinished progress report until the final
completion audit exists and all eleven frozen/control predictions are verified.
Final delivery additionally requires preserved structures/confidence, frozen
published-evidence comparisons at their actual resolution, the flagship stage
trace/discrepancy record, resource accounting, deferred-work record and verified
temporary-worker shutdown. Passing the old development benchmark or producing
an HTML file does not establish completion of the scientific goal.
