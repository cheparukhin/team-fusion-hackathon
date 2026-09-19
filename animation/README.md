# Trans-splicing: a 30-second molecular animation

The MP4 is a silent, captioned 1280 × 720, 24 fps animation lasting exactly 30 seconds. Procedural three-dimensional molecular forms are illustrative, not experimentally resolved atomic structures or molecular dynamics. Colors identify transcript origin, not element type. Time and scale are compressed.

Reference: Venezia et al. (2026), *Functional chimeric mRNAs encode proteins in mammalian immunity*, https://doi.org/10.1038/s41586-026-10982-x.

The animation uses generic Gene A/B, not a structural reconstruction of GSDMD–TMEM106A. In that paper, the TMEM106A-derived portion is translated in a different frame from canonical TMEM106A. Thus the generic orange region should not be interpreted as an intact TMEM106A domain. A translatable open reading frame is required; preserving both parental reading frames is not universally required.

The paper supports spliceosome dependence and CTCF-dependent parent-gene proximity. The exact spatial choreography of RNA joining remains a model. Precursors retain splice substrates; mature mRNAs are not simply glued together. The first scene is one canonical example, not a claim that every gene has exactly one transcript or protein. Trans-splicing is selective and does not guarantee a stable or functional protein.

## Reproduce

Install numpy, pillow and imageio-ffmpeg, then run `python3 render.py`. In this environment dependencies are isolated in `/tmp/chimera_animation_libs`. `python3 render.py --preview` creates a storyboard without rendering the video. No downloaded molecular assets are required.

The editable renderer defines 3D coordinates, perspective projection, depth ordering, shaded molecular spheres, scene transitions and all typography. Output: `trans_splicing_30s.mp4`, `poster.jpg`, `storyboard.jpg`.
