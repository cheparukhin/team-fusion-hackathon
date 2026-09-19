# Cellular edition: 4K / 30 seconds

This version preserves v2's 30-second timeline and minimal labels, while replacing its image-plane renderer with a perspective, depth-buffered OpenGL renderer. Final target: 3840 × 2160 pixels, 24 fps, 720 frames. Geometry is rendered at that resolution rather than upscaling the previous video.

## Visual changes

- Atomic nucleotide templates include sugar, phosphate, and base atoms. Pearly backbones and four base colors follow the supplied visual reference. Base colors are illustrative, not element colors; cyan/orange backbone tints identify RNA origin.
- RNA is continuously attached to the deposited nascent RNA in RNA polymerase II. The visible strand extends along an unobstructed route. Its annotation is positioned separately, below the strand.
- The old schematic ribosome is replaced with the deposited human 80S ribosome, including rRNA and protein subunits. “Translation” is a large scene title.
- Directional key, fill and rim lighting, specular highlights, contact occlusion, restrained bloom, depth-dependent blur and fog replace the flat presentation.
- Distant macromolecules imply a crowded cell interior. They are contextual scenery, not a quantitatively scaled cell reconstruction.
- The final proteins are opaque, smoothly shaded 3D ribbon meshes with depth occlusion, retaining the long comparison hold.

## Structural evidence and templates

| Component | Coordinate source | Use and limits |
| --- | --- | --- |
| Human 80S ribosome | [4UG0](https://www.rcsb.org/structure/4UG0), Khatter et al., *Nature* (2015), 3.6 Å cryo-EM | Deposited heavy-atom geometry, rather than a two-blob placeholder. The animated messenger RNA path and nascent peptide are schematic; this is not a resolved trajectory of translation. |
| RNA polymerase II | [1Y1W](https://www.rcsb.org/structure/1Y1W) | Deposited eukaryotic elongation-complex atoms. Its bound RNA chain anchors the extended nascent strand. It is a yeast structural reference, not a human-specific model. |
| Human spliceosome | [5XJC](https://www.rcsb.org/structure/5XJC) | Deposited pre-exon-ligation complex, now displayed with heavy atoms rather than only representative backbone sites. This is a cis-splicing structure illustrating shared machinery; it is not a resolved trans-splicing complex. |
| DNA nucleotide geometry | [1BNA](https://www.rcsb.org/structure/1BNA) | Deposited nucleotide atom templates arranged into illustrative B-DNA flanks. The extended duplexes are not energy-minimized sequence-specific models. |
| RNA nucleotide geometry | [4UG0](https://www.rcsb.org/structure/4UG0) | Deposited A/C/G/U nucleotide templates placed along schematic polymer paths. Backbone connections, bending and movement are illustrative rather than a molecular dynamics trajectory. |
| Protein A / B ribbons | [1UBQ](https://www.rcsb.org/structure/1UBQ) / [1MBN](https://www.rcsb.org/structure/1MBN) | Same generic teaching references as v2; ribbon geometry follows coordinates and helix/sheet annotations. These are not the parent proteins from PAPER_REF. |

The fusion protein remains an **illustrative composite fold**, explicitly labeled on screen. It uses retained reference fragments from 1UBQ and 1MBN in a new arrangement with a schematic linker. It is neither an experimentally determined fusion structure nor a folding prediction. It does not imply that ubiquitin and myoglobin naturally trans-splice, or that all fusion proteins acquire entirely new folds. A specified fusion sequence would be needed for a sequence-specific model.

Paper context remains [Venezia et al., *Nature* (2026)](https://doi.org/10.1038/s41586-026-10982-x). The animation illustrates the generic idea of selective RNA-level joining and translation; it does not reconstruct the paper's GSDMD–TMEM106A protein.

## Reproduction

Run `python3 animation/v3/render.py --preview` for the 4K frames and storyboard, or omit `--preview` for the MP4. `--one 4.8 --draft` renders a 1080p lighting test only. Final rendering does not use `--draft`.

Dependencies: numpy, scipy, Pillow, gemmi, moderngl, glcontext, imageio-ffmpeg, and an EGL/OpenGL runtime. This environment uses Mesa llvmpipe. The renderer imports the validated ribbon construction from `animation/v2/render.py`, and retains earlier PDB files under `animation/v2/structures`. New coordinate files are under `animation/v3/structures`.
