# Gsdmd:Tmem106a structure evidence

The gallery contains one candidate-specific prediction and a separate experimental parent structure. It does not contain an experimental chimeric-protein structure. The paper's Figure 3a is an AlphaFold3 prediction (server, seed 9999); the new gallery uses a cached, independently generated Boltz2 prediction and is not a reproduction of the author's model coordinates.

## Sequence and experimental reference

The 118-residue sequence is a GENCODE M28 / GRCm39 reference reconstruction of Gsdmd exons 1–2 followed by Tmem106a exons 6–9. Equivalent transcript combinations produce the same sequence. The selected transcripts are ENSMUST00000023238.6 and ENSMUST00000039581.14. The ORF starts at RNA offset 159 (0-based), crosses the junction at offset 379, and has 354 coding nucleotides followed by a stop codon. Its first 73 residues match mouse GSDMD; residues 74–118 are a novel out-of-frame tail. Red therefore means novel sequence encoded across the chimeric junction and downstream RNA, not a transplanted TMEM106A protein domain.

Protein SHA256: `f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa`.

The coordinator independently reproduced this sequence using this project's pinned M28 transcript FASTA and exact 120 nt probe mapping; see `results/presentation/reference_orf_verification.json` and `scripts/presentation/verify_reference_orf.py`. The reconstruction matches published length, N-terminal identity, tail peptide and reported mutation-position constraints. An author-provided full-length sequence file was not retrieved. The sequence is not a discovery made by our 2M-read Parabricks pilot.

[Mouse GSDMD PDB 6N9N](https://www.rcsb.org/structure/6N9N) is an experimental X-ray structure at 3.30 Å. We display chain A only, using deposited author residue numbering. All 69 observed residues within positions 1–73 match the candidate sequence. Positions 1, 71, 72 and 73 are absent from chain A coordinates. These are not filled or grafted onto the candidate. Blue highlights the shared observed parent segment; gray marks the rest of the parent. The crystallographic entry contains two copies; the biological assembly is monomeric. The parent is an autoinhibited GSDMD reference, not a structural template used by this visualization to synthesize the chimera.

## Actual prediction and confidence

The coordinates are imported read-only from the existing `chrna/runs/focused-pilot-20260919` run. Every imported prediction file is checked against the prior run's recorded SHA256. The coordinate residue sequence is then independently checked against the FASTA. Boltz2 2.2.1 ran with one GPU, 3 recycling steps, 200 sampling steps, one diffusion sample, step scale 1.5 and seed 20260919, using its preserved A3M alignment. Recorded model inference took 41.96 seconds; this is prior-run timing, not new execution or a speedup measurement. The original command, timestamps, file hashes, scores and per-residue confidence remain in `gsdmd_tmem106a/cached_inference_provenance.json`.

Mean pLDDT is 48.70/100 and pTM is 0.336; 53.4% of residues have pLDDT below 50. The displayed geometry is a low-confidence model hypothesis. It does not establish a stable fold, structural mechanism, protein expression, function or druggability. Low confidence is also not evidence that the RNA or protein does not exist. No affinity or docking prediction was made.

## Rendering and technology audit

PyMOL renders actual deposited/predicted coordinates as cartoons at 2400 × 1800 pixels, with blue `#0000FF` and red `#D22D27`. PyMOL assigns graphical secondary structure from geometry; this is not an additional experiment. The candidate is one polypeptide chain with source-region coloring, not two protein chains. The comparison panel is 4200 × 2400 pixels. Separate SVGs are vector C-alpha traces, not ribbon cartoons; interpolation is purely graphical, and experimental gaps are disconnected. PNG/PDF comparison views contain ray-traced raster molecules with vector labels in the PDF.

We inspected the installed BioNeMo OpenFold3 NIM and Boltz2 NIM skills first. Hosted NIM authentication keys were unavailable in the inspected environment; no NIM prediction request was submitted. Existing Brev inventory was inspected: the earlier A100 structure host was stopped, and unrelated CPU resources were running. We reused completed local Boltz2 artifacts without starting or altering any instance. New structure compute allocation: $0. This is actual open-source Boltz2 prediction reuse, not an NVIDIA NIM execution claim. Other adjacent cached models belong to a separate pilot and were not substituted for this paper's candidate panel.

No validated complete ORF/prediction is currently supplied for Cd274:Lacc1 or Psap:Lgals3. Their exact RNA-junction/exon diagrams are separately available from `results/presentation/candidate_examples.json`; a 120 nt probe is insufficient to assert a full protein sequence.

## Reproduction

Optional tools are isolated from the model environment:

```bash
uv pip install --python .venv/bin/python --target /tmp/chrna-structure-tools -r scripts/structures/requirements-structures.txt
PYTHONPATH=/tmp/chrna-structure-tools .venv/bin/python scripts/structures/render_structures.py
```

Cached FASTA/CIF/confidence/MSA/provenance are portable within this repository; rendering does not need the adjacent project. To re-import the original cached run and retrieve the RCSB reference, run `scripts/structures/prepare_structures.py --prior-run /path/to/focused-pilot-20260919` with the project Python. This is optional and requires the original run tree.

To independently rerun folding in a compatible GPU Boltz2 2.2.1 environment, run from `results/structures/gsdmd_tmem106a`:

```bash
boltz predict prediction.yaml --out_dir rerun --cache /path/to/verified/boltz/cache --model boltz2 --accelerator gpu --devices 1 --recycling_steps 3 --sampling_steps 200 --diffusion_samples 1 --step_scale 1.5 --seed 20260919 --write_full_pae
```

The preserved `input.yaml` is historical provenance; portable `prediction.yaml` uses the colocated `msa.a3m`. Reruns may differ across hardware/software, and this command requires a separately authorized GPU allocation.
