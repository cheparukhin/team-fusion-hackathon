# Reproduction execution

The full objective remains [execution_goal.md](execution_goal.md). The current
implementation covers verified cohort intake, pinned GENCODE reference
transfers, reference compatibility checks, and complete pilot FASTQ/name
validation. It does **not** yet complete a sample's caller analysis, freeze discovery,
reconstruct proteins, predict structures, or produce the scientific HTML report.

Use one active operator per task. Snakemake holds its working-directory lock;
reference transfers also take a nonblocking per-file OS lock. Do not remove a
lock merely because an observation timed out. Check the live process before
resuming a task. Queue additional operator requests in the run record instead
of starting another instance of the same job.

## Controller commands

The existing pilot and the reproduction controller share the Python package.
The recorded controller environment is `workflow/requirements-controller.txt`
(Python 3.12.3, Linux x86_64). Install it into an isolated virtual environment,
then install this project with `pip install -e . --no-deps`. This environment
does not include the scientific worker tools.

```bash
export XDG_CACHE_HOME=/srv/chrna-team/project/.cache
export MPLCONFIGDIR=/srv/chrna-team/project/.cache/matplotlib
.venv-reproduction/bin/snakemake --snakefile workflow/Snakefile --cores 1
.venv-reproduction/bin/snakemake --snakefile workflow/Snakefile --cores 1 references
.venv-reproduction/bin/snakemake --snakefile workflow/Snakefile --cores 1 reference_audit
.venv-reproduction/bin/python scripts/install_sra_toolkit.py
.venv-reproduction/bin/snakemake --snakefile workflow/Snakefile --cores 2 pilot_intake
.venv-reproduction/bin/pytest -q
```

The default target builds the cohort manifest. The explicit `references` target
downloads the three declared GENCODE M28 files, checks publisher MD5 values,
and records SHA-256 receipts. Snakemake resumes completed targets; interrupted
individual reference transfers restart into a `.partial` file. A partial or
checksum-failing file is never promoted to a verified reference.

`reference_audit` rechecks downloaded hashes and compares genome coordinate
bounds, annotation transcript IDs, transcript FASTA IDs, exon-derived lengths
and biotype coverage. Its report explicitly separates compatibility problems
from downloaded-file integrity. It does not prove base-by-base reconstruction
identity and must not be presented as a completed reconstruction test.

Pilot intake jobs have explicit timeouts, exclusive task locks, and immutable
attempt directories. Completed attempts are reused only for matching commands.
Running/failed attempts are not automatically restarted. Inspect their actual
process handle and preserve failures before creating a new attempt. The local
job wrapper is not a Brev lifecycle controller and does not authorize launches.

Snakemake owns stage receipts; the adapters own raw archives, FASTQ, name exports
and detailed QC records, so workflow retries do not delete those evidence files.
The QC stage rechecks the FASTQ hash and independently verifies all submitted
names and lengths against SRA NAME/READ_LEN before final validation.

The initial SRA/GEO responses and their retrieval timestamps and SHA-256 values
are in `runs/intake-20260919/`. Changes to those responses require a new intake
directory. The manifest verifies ten distinct run/sample identities and their
cross-references, preserves the archive's `cDNA` selection field, and establishes
direct-RNA chemistry from each sample's protocol. Raw signal availability remains
unverified. Pilot submitted-name retention has been checked against the archive;
the other nine samples have not been extracted.

The pilot is the complete SRR28984805 / GSM8260877 sample (steady-state replicate
3), selected by smallest reported archive size without candidate or outcome
information. Its archive has 2,238,871 spots and 1,966,956,471 bases. Full-cohort
execution remains gated on a successful complete-sample run and measured
resource use.

The complete pilot input passed validation: 2,238,871 reads and 1,966,956,471 bases,
with no missing submitted names, duplicate submitted names, or mismatches in the
independent name/length crosswalk. Extraction took 130.6 seconds; its measured
child-process peak RSS was 414,744 KiB. This is intake resource use, not the caller
pipeline's resource requirement. See `runs/pilot-20260919/intake_validation.json`
and its linked QC reports and job records. No junctions have yet been recovered.

## Scientific worker environment

`workflow/envs/typhon-linux-64.explicit.txt` locks 388 package URLs/builds with
MD5 values, and the adjacent JSON records SHA-256 values. All installed packages
and downloaded package archive SHA-256 values were verified. Installation and
solve attempts are retained in `runs/worker-environment-20260919/`.

The installed versions include minimap2 2.24-r1122, SAMtools 1.15 (with HTSlib
1.17), LongGF 0.1.2 and BLAST 2.13.0. Required Python and R imports pass. The
locked R runtime is 4.2.2; packages built under 4.2.3 issue warnings, preserved in
`r-import-warnings.log`. Full caller execution is still required to establish
runtime compatibility.

Genion 1.2.3 source commit `f78d5b92d43439925040c72b2c5ea96abbef472d` was patched
with the recorded TYPHON read-ID patch (zero fuzz) and an explicit `cstdint`
include for compiler compatibility. It compiles and reports
`1.2.3-typhon2179e9d`. JAFFAL 2.3 source and Bpipe 0.9.9.2 are pinned separately;
the four JAFFAL utilities compile, and its singleton setting is one read.
JAFFAL reference integration, sample-specific historical version assignments,
Genion reference preparation and synthetic caller controls remain unfinished.

The RNA-only exact-junction ranking module has implementation tests. Its
[draft specification](rna_ranking_draft.md) is not a production scientific freeze.

## Compute prerequisite

The initial Brev check was logged out. A fresh `brev org ls` check succeeded at
15:01 UTC on 2026-09-19; the agent did not change authentication or service
settings. Live inventory shows only `chrna-controller`, and a CPU-worker search
response is saved in `runs/worker-environment-20260919/`. No new worker has been
launched. Resolve quote currency and existing-resource costs, refresh quotes
immediately before a launch, check the combined rate with `scripts/check_budget.py`,
and finish the bounded remote-job controller before provisioning.

The observed local environment has 2 CPUs, approximately 8 GiB RAM, and roughly
107 GiB free disk. It is suitable for controller development and metadata work;
it does not meet TYPHON's documented 64-GiB worker requirement. Docker daemon
access was denied. Scientific worker execution validation, shutdown-on-failure logic,
output preservation, and resource accounting still need implementation and
verification before provisioning.

## Verification and remaining gates

Existing `chrna fetch`, `chrna build`, and development-only `chrna benchmark`
remain regression checks for the older published-table pilot. They are not
evidence of raw-read reproduction. No held-out benchmark was requested.

1. Finish JAFFAL references/version mapping, caller integration, synthetic
   controls and remote controller preflight. Intake/reference checks are complete.
2. Implement and test both paper-method and evidence-assessment branches; run
   the complete pilot with measured CPU, memory, disk and runtime.
3. Run all ten mouse samples. Preserve every proposal and decision, validate
   transcript competition including noncoding transcripts, rank exact junctions,
   and freeze inputs, exclusions, rules and ranked evidence before comparison.
4. Reconstruct observed/consensus/reference-assisted RNA alternatives and
   continuously translated junction-spanning ORFs with nucleotide provenance.
   Complete Boltz-2 ensembles for every distinct eligible sequence with an
   explicit failure/eligibility ledger. Implement the prespecified structural
   cross-check and report inaccessible AlphaFold 3 or author-coordinate inputs.
5. Join paper references at their actual resolution after freezing. Produce
   per-example stage traces, the flagship discrepancy analysis, RNA/protein
   FASTAs, structure artifacts, and HTML exon/ORF views. Keep review decisions
   separate. Add the depth-matched SG-NEx protocol comparison after the core
   works; protocol groups remain observational categories.

No candidate-level scientific decisions have been frozen at this checkpoint.
