# TYPHON source audit: initial findings

Inspected commit: `2179e9daa445f055c5b228ed6f7b33c2373ed765`.
The source archive and inspected-file hashes are recorded in
`runs/intake-20260919/typhon_source_record.json`. No upstream scripts were executed.

| Location | Observed behavior | Required handling |
|---|---|---|
| `typhon/modules/run_longgf.py:122` | Genome alignment uses `--secondary=no -G 50k` | Preserve for the paper branch; obtain separate ambiguity-aware alignments for the audit branch. |
| `config_template.yaml` | LongGF, Genion and JAFFAL allow one supporting read | Preserve singletons and retain caller output before later filtering. |
| `typhon/modules/exon_repair/transcript_selection.py:204` | Drops retained-intron transcript matches | Do not apply this exclusion to the audit's comprehensive single-transcript comparison. |
| `typhon/modules/exon_repair/transcript_selection.py:208` | Restricts matches to proposed parental genes | Search other known transcripts when testing competing explanations. |
| `typhon/modules/exon_repair/transcript_selection.py:305` | Selects one transcript per gene/read | Preserve plausible alternatives separately in reconstruction. |
| `environment.yml` | Most scientific dependencies have no version pin | Resolve explicit versions/builds before worker execution. |
| `LICENSE` | CC BY-NC 4.0 with research-use restriction | Retain attribution and licence; audit third-party licences independently. |

The [paper methods](https://www.nature.com/articles/s41586-026-10982-x#Sec7)
describe TYPHON as a reimplementation of the manual analysis. They specify
LongGF 0.1.2, Genion 1.2.3, minimap2 2.24, and JAFFAL 2.2/2.3, with matched UCSC
resources for JAFFAL. Exact per-sample JAFFAL version assignments remain unknown.
The Genion read-ID patch needs validation against both the source implementation
and its emitted records. This initial audit does not establish caller fidelity.

The patch now applies to Genion tag 1.2.3 without fuzz, and the patched source
compiles; emitted scientific records still need fixture validation. The installed
LongGF usage text documents pseudogene setting `2` as no filter, whereas the
TYPHON configuration comment calls it moderate. Preserve the actual numeric
paper setting and use the executable semantics in the audit.

The [GENCODE M28 release](https://www.gencodegenes.org/mouse/release_M28.html)
provides the genome, comprehensive annotation and transcript FASTA specified in
`workflow/references.json`. Compatibility checks must precede alignment.
