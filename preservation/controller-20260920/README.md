# Controller integration and evidence data

Newer work from `chrna-controller` has been integrated into the existing project.
Superseded remote copies of the ranker, submission, dashboards, and packaged
repositories were discarded. The previous duplicate recovery source tree has
been removed. There is one maintained location for each workflow:

| Work | Code and current summaries |
| --- | --- |
| Structure, disorder, diversity, and Gsdmd cross-model analysis | [scripts](../../scripts/structure_campaign/README.md), [results](../../results/structure_campaign/RESULTS.md), root `tests/` |
| Mouse and K562 analysis, including literature-candidate tracing | [existing mouse/K562 workflow](../../workflows/mouse-pilot/README.md) |
| Partial cross-species liver comparison | [cross-species workflow](../../workflows/cross-species/README.md) |
| Ranking, review demo, primary dashboard, and submission | Existing reviewed entry points in [START_HERE](../../START_HERE.md) |

The reviewed ranker, metrics, and current submission remain authoritative.
Distinct experiment evidence is retained, including unsuccessful/partial runs;
that does not establish completion, translation, protein function, or a new
ranking gain.

## Large files live outside Git history

Download the three numbered data parts from the
[controller evidence release](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/controller-preservation-2026-09-20).
GitHub release assets provide the separate large-file storage; no LFS account,
large Git blobs, or history rewrite is required. The two asset groups identify
the source folders, not additional project versions.

The release holds 2,500 unique files (7,525,885,841 uncompressed bytes): saved
alignments/read evidence, model coordinates and confidence arrays, MSA inputs,
full disorder profiles, reference mappings, figures/report assets, K562 and
partial full-mouse results, cross-species outputs, and the latest v4 animation.
Another 1,071 required paths are reconstructed from identical content already
in the repository or archives, instead of storing duplicate payloads.

[Archive parts and checksums](archives.json) · [data file checksums](files.tsv) ·
[file decisions](file-dispositions.tsv) · [validation](validation.json)

## Restore into the existing repository

Download every `controller-*.tar.gz.part-*` asset into one directory. From the
repository root, run:

```sh
python3 preservation/controller-20260920/restore.py --assets /path/to/downloads
python3 preservation/controller-20260920/verify.py .
```

Python's standard library is sufficient. The restore command verifies all
archive checksums, every contained file, safe paths, and duplicate-content
sources before writing. It places evidence at the paths the code uses, such as
`results/structure_campaign/`, `workflows/mouse-pilot/runs/`, and
`workflows/cross-species/`. It refuses to overwrite a differing existing file.
Repeated restores with unchanged files are safe. Restored large data are ignored
by Git; only source, selected summary tables, documentation, and manifests are
versioned.

To inspect the current structure report after restoration:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/results/structure_campaign/report/`. To replay
saved model integrity checks (requires `numpy` and `gemmi`):

```sh
python3 scripts/recovery/verify_quick_hack.py --root .
```

Original provenance fields may retain controller/worker paths. External tools,
model weights, and public raw-read downloads must be installed or fetched for a
full scientific rerun; restoration alone does not run analyses or provision
compute. See each canonical workflow's instructions.

## Inputs and exclusions

Raw public sequencing/Hi-C downloads, large rebuildable reference/index databases, model weights, installed runtimes and credentials are excluded. Source accessions, pinned inputs, derived evidence and reconstruction methods are retained where available. Distinct partial or unsuccessful experiment records remain labeled as such.

[File checksums](files.tsv), [input dispositions](file-dispositions.tsv), and [verification](validation.json) support provenance and reproducibility. These checks establish artifact integrity, not biological validity.
