# Chimeric RNA structure dashboard

[Public hosted dashboard](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site) · [Local viewer](index.html)

This portable snapshot links RNA/exon origin to eleven predicted structures: ten frozen mouse pilot hypotheses and one separately reconstructed Gsdmd–Tmem106a literature reference control. The control was **not recovered by the pilot**. The ten pilot hypotheses are single-read candidates from SRR28984805; none is established to produce a functional protein.

## View

From the repository root:

```sh
python3 scripts/demo/serve.py
```

Open `http://127.0.0.1:8000/dashboard/`. No API key, GPU or Python package installation is needed. The structure renderer uses pinned **3Dmol 2.5.3** from jsDelivr, so internet is required for 3D rendering. Select a candidate, choose an exon and click a residue to inspect its origin and confidence. Transcript choice and reference-assisted reconstruction are hypotheses, not experimentally established isoforms.

## Rebuild

```sh
python3 dashboard/build.py
```

The standard-library builder works from any current directory. It uses `source/` templates and frozen `inputs/`, verifies all eleven model sequences against their protein hashes, checks residue numbering, confidence lengths and ORF lengths, and writes `index.html`. Rebuilding does not download data, call a model or start compute. PDB coordinates and confidence arrays are embedded in `source/predicted-structures.html`. The standalone wrapper preserves the original security policy and host bridge.

[Provenance and input hashes](provenance.json) record the imported sources and portability edits. The local viewer is a rebuild of the recovered presentation dashboard; it is not asserted to be byte-identical to the separately deployed Sites application. The broader pilot source and frozen run are in [workflows/mouse-pilot](../workflows/mouse-pilot/README.md); these newly recovered annotations and control audit are bundled here so the display rebuild is self-contained.

This is the FINAL tab’s dashboard contribution. The hosted dashboard is available at the link above; the repository also contains the portable local viewer. Sequence identity and deterministic rebuild checks support reproducibility. Prospective usefulness for choosing experimental targets has not been measured. [Scientific scope](../docs/submission/README.md).
