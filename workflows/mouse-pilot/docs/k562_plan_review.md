# K562 plan review — 2026-09-19

Verdict: retain SG-NEx K562 and the RNA-first scope. The earlier plan needed a non-circular evaluation design, explicit implementation gaps and measured input sizing before it could guide execution. Updated plan: [k562_human_pilot_plan.md](k562_human_pilot_plan.md).

| Finding | Evidence | Resolution in reviewed plan |
| --- | --- | --- |
| Corroboration could leak into ranking | `junction_ranking.py` ranks by biological sample count | Freeze replicate-4 ranking before replicate-5/Illumina joins; combined catalogue is descriptive |
| A fixture rerun was too weak a reproducibility claim | Earlier plan allowed a generic deterministic fixture | Add real-read end-to-end subset rerun; state its limited scope |
| Illumina is a new workflow, not a reused mouse stage | Existing pilot is minimap2/LongGF direct RNA | Separate checkpoint B, specify STAR route and prerequisite tests/configuration |
| Adapter absence was not checked | `pilot_assessment.py` has no dedicated adapter scan | NOT_ASSESSED unless a validated annotation is added; never call mapping-supported artifact-free |
| LongGF association was finer-grained in prose than in code | `pair in membership.get(read,set())` assigns LongGF source | Label pair-level association; exact-breakpoint agreement requires reconciliation |
| Human port has more than reference-name changes | Fixed sample IDs/counts/paths and `-G50k`; ranker requires biological IDs | Parameterize acceptance/workflow, retain inherited limitation, handle unknown specimens explicitly |
| Input scale was unmeasured | Four selected public FASTQ HEAD requests returned 200 | Record 2.06 GB direct RNA plus 9.68 GB paired Illumina; no raw downloads performed |
| Release/protocol provenance was underspecified | SG-NEx release notes distinguish AWS replacement files and manifest ENA metadata | Pin commit/file hashes and actual basecalling provenance; retain kit/spike-ins |
| Candidate overlap was not an evaluation specification | No fixed ranking budget/baseline | Frozen A pool, read-count baseline, top-20 reported corroboration with analytical ties; descriptive not biological accuracy |

Remaining pre-execution gates: specimen relationships, exact source/reference freeze, disk/RAM/time/cost worksheet, human parameterization, independent Illumina adapter and frozen settings, meaningful fixtures/regression. No new analysis tests were executed because this task changed documentation only. File checks and live public HTTP metadata checks were performed; compressed files were not downloaded or integrity-validated.

Primary documentation: [SG-NEx](https://github.com/GoekeLab/sg-nex-data), [manifests](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/samples.tsv), [Illumina manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/illumina_samples.tsv), [STAR](https://github.com/alexdobin/STAR). Scientific interpretation follows the existing project data contract and the implemented mouse mapping rules, not a new biological validation claim.
