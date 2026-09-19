# Revised molecular storyboard

## Timing (30 seconds total)

| Time | Image / action |
| --- | --- |
| 0–1.8 s | Separate title: Central dogma |
| 1.8–5.5 s | RNA polymerase II with a physically connected, extending nascent RNA |
| 5.5–9.5 s | Mature RNA translated into protein A (RNA processing is elided) |
| 9.5–11.5 s | Separate title: Chimeric mRNA |
| 11.5–18.1 s | Two distinct precursor RNAs approach the spliceosome; compatible segments align |
| 18.1–20.5 s | Joined cyan/orange RNA is held in view |
| 20.5–24.5 s | Chimeric mRNA translated into a connected polypeptide |
| 24.5–30 s | Sustained side-by-side ribbon comparison: A, B, illustrative fusion |

Export, chromatin contacts, nuclear membranes, cap/poly(A) processing, and detailed canonical intron removal are excluded. Labels replace paragraph captions. No implication that transcription and translation occur simultaneously in one compartment: these are separate shots.

## Actual coordinate sources

- Spliceosome: [PDB 5XJC](https://www.rcsb.org/structure/5XJC), human spliceosome just before exon ligation, cryo-EM, 3.6 Å. The rendering uses deposited C-alpha and RNA backbone coordinates in their original relative arrangement. This is a real **cis-splicing** complex used to illustrate the shared machinery, not an experimentally determined trans-splicing complex. The foreground precursor RNA paths and ligation are explanatory schematics, not a molecular dynamics simulation. Subunits are not invented spheres or randomly positioned clusters.
- Polymerase: [PDB 1Y1W](https://www.rcsb.org/structure/1Y1W), complete yeast RNA polymerase II elongation complex. The nascent RNA is continuous with the modeled RNA chain P and extends from its 5′ end; the polymerase retains the growing 3′ end. The extended RNA and DNA flanks are schematic. It is a eukaryotic structural reference, not a human-specific model.
- Protein A ribbon reference: [PDB 1UBQ](https://www.rcsb.org/structure/1UBQ), ubiquitin. C-alpha coordinates and deposited helix/sheet annotations determine the cartoon.
- Protein B ribbon reference: [PDB 1MBN](https://www.rcsb.org/structure/1MBN), myoglobin. C-alpha coordinates and deposited helix annotations determine the cartoon. Myoglobin is predominantly alpha-helical; beta sheets are not invented for it.

The generic A/B structures are visual teaching references. They are not the paper's parent proteins or a claimed naturally trans-spliced pair. The fusion illustration joins retained reference fragments (1UBQ residues 1–64 and 1MBN residues 30–130) with a schematic linker in a different relative arrangement. It is **not** a PDB structure, structure prediction, energy-minimized model, or experimentally supported fold. Its different silhouette illustrates one possible outcome, not a rule that every fusion must refold completely. It is labeled “Illustrative fold” on screen. No sequence-specific folding claim can be made without defining the RNA junction and resulting ORF.

The ribosome is a simplified two-subunit illustration. RNA processing is elided between the transcription and canonical translation shots. All sizes and reaction times are illustrative.

## Paper context

[Venezia et al., Nature (2026)](https://doi.org/10.1038/s41586-026-10982-x) supports spliceosome-dependent formation of selected chimeric RNAs and demonstrates protein coding for Gsdmd–Tmem106a. This animation preserves generic A/B names and does not reconstruct GSDMD–TMEM106A. In the paper the TMEM106A-derived region is translated in a different frame from its canonical protein. A productive open reading frame, not necessarily preservation of both parental frames, is needed.

## Rendering

Run `python3 render.py --preview` for the storyboard; `python3 render.py` renders the storyboard and video. Dependencies: numpy, scipy, pillow, gemmi, imageio-ffmpeg. Output is 1600×900, 24 fps, 720 frames. Downloaded PDB coordinate files are retained under `structures/` for reproducibility.
