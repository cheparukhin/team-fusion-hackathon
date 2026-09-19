# Start here: chimeric-RNA project

Canonical workspace: `/home/ubuntu/workspace/chrna` on `chrna-controller`.
Compatibility path: `/srv/chrna-team/project` points here. Existing running jobs and saved task paths can continue using that alias. This is one live project, not a second copy.

The focused pilot is complete: [verified report](reports/focused_pilot.html),
[completion audit](runs/focused-pilot-20260919/completion-audit.json), and
[resource/shutdown record](runs/focused-pilot-20260919/resource-accounting.json).
There are ten frozen reference-assisted protein hypotheses and one separate
published architecture control, with eleven locally verified predictions.
Temporary workers are stopped; the shared controller remains available. Protein
expression/function and de novo recovery of Gsdmd–Tmem106a are not established.

## Read in this order

1. [Current execution goal](docs/execution_goal.md) — owner-approved focused scope, selection rules, deadline, budget, Full Access and end-to-end responsibility.
2. [Project instructions](AGENTS.md) — scientific integrity and resource constraints.
3. [Decision history](docs/context/decision_history.md) — why the plan changed and which earlier proposals are superseded.
4. [Focused pilot rules](docs/focused_pilot_rules.md) — operational scientific criteria. Preserve the frozen version when applicable.
5. [Data contract](docs/data_contract.md) — provenance, label semantics and leakage constraints.
6. [Execution runbook](docs/reproduction_runbook.md) — commands and environment details. Its earlier full-cohort scope and readiness statements are historical; the execution goal and fresh run records take precedence.

The [focused execution runbook](docs/focused_pilot_runbook.md) documents the
current discovery acceptance, Snakemake assessment/ORFs, shortlist freeze,
cached MSAs, bounded Boltz worker and reporting commands.

## Live state and outputs

- [Teammate progress handoff](PROGRESS.md): current completion and compute state after path migration.
- [Focused checkpoint](runs/focused-pilot-20260919/checkpoint.json): read its timestamp and reconcile with newer attempt records.
- [Current repaired pilot attempt](runs/focused-pilot-20260919/retry-2/worker-controller.json) and [controller log](runs/focused-pilot-20260919/retry-2/controller.log).
- [Connectivity diagnosis](runs/focused-pilot-20260919/connectivity-debug/diagnosis.json): Brev SSH needs `SHELL=/bin/sh` under the service account; the pipeline applies this automatically.
- [Active folding attempt](runs/focused-pilot-20260919/active-folding-attempt.json): inspect its controller log and lifecycle records before acting. The initial GPU attempt stopped at the disk-capacity guard; [the diagnosis](runs/focused-pilot-20260919/gpu-storage-diagnosis.json) records the observed storage and priced retry.
- [Pilot intake validation](runs/pilot-20260919/intake_validation.json): 2,238,871 validated reads in SRR28984805.
- [Progress/report HTML](reports/focused_pilot.html): inspect its status; a progress page is not a finished scientific report.
- `runs/focused-pilot-20260919/assessment/`, `orfs/`, and later structure outputs appear as stages finish. Their absence is not a zero-candidate result.
- `src/`, `scripts/`, `workflow/`, `tests/`, `infra/` contain the actual runnable implementation and budget/lifecycle controls. `data/` contains inputs, reference data and provenance; do not redownload or duplicate validated inputs.

Never infer current status from the historical proposal, an old checkpoint, or a synthetic test. Do not start a second controller while the current attempt is active. Preserve the workflow lock and consult live process/lease records.

## Reference context available offline

- [Google planning document snapshot](docs/context/source-snapshots/google-plan-20260919.md): all tabs, source URL and revision. Several hypotheses and old exclusions are superseded; this is reference material.
- [Scientific discussion snapshot](docs/context/source-snapshots/scientific-discussion-20260919.md): scientific requests and proposals from the original discussion; personal access details and abandoned server setup omitted.
- [Historical detailed technical proposal](docs/context/source-snapshots/technical-proposal-historical.md): full original design; not tonight's scope or spending authority.
- [Archived full-scope execution goal](docs/execution_goal_full_scope_20260919.md): retained for provenance only.
- [Study run manifest](docs/context/evidence/sra-run-manifest.csv) and [archive summary](docs/context/evidence/archive-summary.json): 10 study runs / 52,903,853 reads; only the pilot is required tonight.
- [Scientific plugin setup](docs/context/science-plugins.md): installed tools and access limitations; no credentials included.
- [Data source registry](data/sources.json), [data audit](reports/data_audit.json), and original supplementary tables under `data/raw/`.
- [Paper HTML](data/raw/published_control/article.html) and [provenance](data/raw/published_control/article.html.provenance.json). Published-control sequences/figures are separate from de novo recovery.

Paper: https://www.nature.com/articles/s41586-026-10982-x
TYPHON: https://github.com/erenada/TYPHON

## Shared execution

Join with `brev shell chrna-controller`, then `tmux attach -t chrna-codex`.
The saved task is `01a0ba08-d9ef-7a23-9451-e72327b577d8`.
Configuration requested by the owner: Astra medium, normal speed/Fast off, Default execution mode, Full Access, active persistent goal. Verify live task status when resuming. Teammates take turns typing into the same terminal.

End-to-end means actual analysis, defensible sequence reconstruction, selected structures, verification, report delivery and worker shutdown—not only writing scripts. Delivery target is 23:00 Europe/London on 19 September 2026; stop new additions at 21:00 and temporary compute by 22:00. Preferred combined Brev rate is below USD 100/hour; hard ceiling USD 500/hour. Refer to the live goal for full rules.

Secrets, API keys and login caches remain outside the project. No custom dashboard, bearer-token distribution or new team authentication system is part of this task.
