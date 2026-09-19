# Project progress

Updated 2026-09-19 at 17:01:06 UTC. Compute state last verified at 17:00 UTC.
Canonical workspace:
`/home/ubuntu/workspace/chrna`. Latest owner instruction requests a safe checkpoint
and controller-managed restart; this instance is now waiting for that restart.
The launcher is `scripts/shared_codex.sh`; the old `/srv`
compatibility path and cached paths remain intact.

Current work: restart checkpoint and documentation are finished. No analysis job
is pending. Blockers: none for the completed focused goal. Next steps: controller
resumes this same thread at the canonical path; retain the
report and frozen outputs for team review; any additional scientific work is
listed under deferred work below. Update this file at meaningful milestones with
UTC time, completed/current work, findings, limitations, blockers and next steps.

## Restart checkpoint: PATH_MIGRATION_READY

Local process inventory at 17:01 UTC found no live project analysis or transfer
processes. PID 119998 is absent. All current file writes are complete; no new
analysis jobs were launched and no processes were stopped. Native goal status
remains `complete`; its objective and budget have not been changed.

Preserve these existing teammate services through the Codex restart:

- PID 128299: report HTTP server on localhost port 8765, serving `reports/`.
- PID 165746: teammate dashboard HTTP server on localhost port 4173, serving
  `demos/chimera-dashboard/dist/`.
- PID 77277: shared `chrna-codex` tmux server/session. Leave unrelated SSH,
  editor and other Codex sessions untouched.

Those HTTP services are children of a separate app server (PID 17160), not this
shared Codex process (PID 129492). No scientific subprocess requires survival.
On resume, read this file and the completion audit before acting; do not rerun
the completed pilot or provision compute merely to service the restart.

## Existing goal: complete

The same focused execution goal (thread `01a0ba08-d9ef-7a23-9451-e72327b577d8`)
is already complete. Its scope, progress and resource constraints are preserved.
The migration handoff did not launch another controller or expand the study.

- [Delivered report](reports/focused_pilot.html): 116 supported RNA junctions,
  ten frozen protein hypotheses and one separate published architecture control.
- [Completion audit](runs/focused-pilot-20260919/completion-audit.json) and
  [continuation checkpoint](runs/focused-pilot-20260919/checkpoint.json): no
  outstanding work within the focused goal.
- [Structure verification](runs/focused-pilot-20260919/structures/summary.json):
  eleven preserved predictions locally verified, zero failed or deferred.
- [Validation commands](runs/focused-pilot-20260919/validation-commands.json):
  101 tests passed; reproducible data build and development benchmark passed.
- [Final report validation](runs/focused-pilot-20260919/final-report-validation.json):
  110 internal links checked. Report SHA-256 was rechecked at this handoff and
  matches `dff44f27c23b6f8bf44c330349af30758556ff048cce0e99652f1b4d7af78f33`.

All ten selected hypotheses have singleton read support and use reference-assisted
sequence reconstruction. Protein expression and function remain UNKNOWN. Gsdmd–Tmem106a
was not recovered de novo; its separate control matches published architectural
constraints. File verification does not establish structural accuracy. Unreported
published support remains UNKNOWN, and held-out outcomes were not used for ranking.

## Compute handoff

Live `SHELL=/bin/sh brev ls --json` at 17:00 UTC confirmed:

| Resource | State |
| --- | --- |
| `chrna-pilot-cpu-20260919` (`6k9lx0737`) | STOPPED |
| `chrna-boltz-20260919` (`8mq2074bp`) | STOPPED |
| `chrna-controller` (`2gnfmgobs`) | RUNNING; shared controller retained |

Detached CPU controller PID 119998 has exited. Its
[retry-2 lifecycle record](runs/focused-pilot-20260919/retry-2/worker-controller.json)
records success and worker shutdown. The final GPU attempt is
`folding-worker-retry-3`, with shutdown confirmed at 16:54:43 UTC.
The filename [active-folding-attempt.json](runs/focused-pilot-20260919/active-folding-attempt.json)
is a pointer to that terminal attempt, not evidence of a running job.

[Resource accounting](runs/focused-pilot-20260919/resource-accounting.json)
preserves the launch quotes and shutdown evidence. Preferred combined rate remains
below USD 100/hour and the absolute ceiling USD 500/hour; these are rate limits,
not a spending target. No further compute is required for the completed goal.
Do not duplicate the pilot or restart stopped workers to inspect their outputs;
the verified outputs are local. Any future authorized launch requires fresh prices
and resource checks. Brev transport requires scoped `SHELL=/bin/sh`.

## Future work

[Deferred work](runs/focused-pilot-20260919/deferred-work.json) is outside the
completed focused scope. Preserve the frozen selection and its provenance. Consult
[START_HERE.md](START_HERE.md) and [the execution goal](docs/execution_goal.md)
before any newly requested analysis.
