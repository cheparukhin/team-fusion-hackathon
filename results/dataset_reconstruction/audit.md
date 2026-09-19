# Dataset reconstruction audit

Reproduction: `PYTHONPATH=src .venv/bin/python -m chrna.data --root .` (cached, offline). Add `--download` only for missing inputs.

## Frozen counts

```json
{
  "raw_probe_designs": 529,
  "mapped_unique_panel_pairs": 527,
  "eligible_probe_designs": 481,
  "probe_designs_with_pair_level_support": 111,
  "short_read_supported": 287,
  "nanostring_supported": 109,
  "cross_supported": 13,
  "exact_nanostring_panel_matches": 107,
  "sequence_resolved_nanostring_panel_matches": 109,
  "sequence_verified_suffixes": 5,
  "table3_read_rows": 36826,
  "table3_unique_reads": 36826,
  "table3_unique_pairs": 30390,
  "unique_junctions": 31634,
  "probe_junctions_uniquely_mapped": 529,
  "eligible_model_pairs": 479,
  "eligible_model_positives": 109,
  "excluded_panel_pairs": 48,
  "sample_count_available": 0
}
```

## Labels, exclusions, and assay uncertainty

The target is membership in Supplementary Table 7's NanoString-supported ordered gene-pair list within the mapped biological probe panel. Zero means **not reported supported**, never a demonstrated false RNA or failed assay. Table 8 supplies designs, not individual assay testing or QC results; both statuses remain unknown even for reported positives. Pair support is not propagated as junction-specific validation.

The exact panel join is 107 of 109 positives. Aoah:Sirt5_2 and Tbc1d23:Xdh_2 resolve to Aoah:Sirt5 and Tbc1d23:Xdh because BOTH ordered 60-nt probe halves exactly match the named M28 parent transcripts. The same independent sequence check resolves Slc25a13:Sem1_2, Plekhm2:4930455G09Rik_2, and Slc16a10:Rpf2_2. All five unsuffixed pairs also occur in Table 3. Slc25a13:Sem1 and Slc16a10:Rpf2 each have both a base and a _2 design, so 529 designs collapse to 527 ordered pairs, and 481 eligible designs collapse to 479 model pairs. Original IDs and every matching transcript remain in probe_panel.tsv and probe_sequence_mapping.tsv. All 529 sequences pass both parent-half matches. The suffix is not removed without this evidence.

48 panel pairs are absent from Table 3 and all three Table 4 caller lists. The article mentions scrambled controls but neither these tables nor their cell formatting identifies individual controls. These 48 are conservatively excluded as unresolved biological candidate/control status, NOT asserted to be controls. Their read support is missing, not zero. This additional catalogue restriction may affect generalizability and is reported explicitly. No label-dependent exclusion rule is used.

## Read and sample handling

Table 3 has 36,826 globally unique read IDs and 30,390 ordered pairs. Counts union unique read IDs within each ordered pair across observed junctions. Table 4 provides caller membership only; its rows are never added as extra read support. read_evidence.tsv preserves each source row and read ID; junctions.tsv groups exact published coordinate/strand tuples. Table 1 identifies 10 biological samples but does not link them to read IDs; sample_count/sample_ids remain unavailable for every pair. Caller-specific or inferred sample assignments are not fabricated.

## Coordinates and parent identity

Pinned GENCODE M28 gene intervals use GRCm39, 1-based inclusive coordinates. genomic_distance is the minimum absolute base-coordinate separation between any parent intervals; overlap=0, interchromosomal=0 with is_interchromosomal=1. Multiple GENCODE records with the same symbol are retained together only when their MGI identity, chromosome and strand agree; all stable IDs remain present. Distinct unresolved identities are excluded from modeling. This handles Ndor1, Nnt, Aldoa, and Dpep2 without choosing an arbitrary Ensembl ID.

junctions.tsv preserves Table 3 breakpoints exactly; their base-origin convention is not explicitly specified in the spreadsheet. probe_junctions.tsv independently maps the final nucleotide of the first 60-nt parent half and the first nucleotide of the second half through M28 transcript exons into 1-based inclusive genomic positions. Only unique coordinate tuples across transcript matches are exported. Multiple matching transcripts with identical coordinates are harmless. Probe coordinates are suitable for assembly-matched binning; pair-level labels do not establish the validity of every observed junction. Exact cross-table breakpoint comparison must account for documented convention ambiguity.

## Feature availability and leakage prevention

Only long_read_support, sample_count (unavailable), is_interchromosomal, and genomic_distance are proposed RNA predictors. Short-read and NanoString flags, plate, probe sequences, and names are evidence/metadata only. Missing read support is never zero-filled. Preprocessing and gene-disjoint fold construction are the classifier's responsibility.

## Excluded probe IDs

- Ogdh:Rabep1: unresolved_biological_candidate_or_control
- Osbpl8:Spty2d1: unresolved_biological_candidate_or_control
- Uxt:Pi4k2a: unresolved_biological_candidate_or_control
- Btrc:Fbxw4: unresolved_biological_candidate_or_control
- Gramd1a:Xdh: unresolved_biological_candidate_or_control
- Polrmt:Ppp2r2a: unresolved_biological_candidate_or_control
- Trim14:Uqcrh: unresolved_biological_candidate_or_control
- Zfyve27:Prpf4b: unresolved_biological_candidate_or_control
- Ctsb:Clec2d: unresolved_biological_candidate_or_control
- Mrpl40:Sh3bgrl3: unresolved_biological_candidate_or_control
- Msrb1:Mir155hg: unresolved_biological_candidate_or_control
- Mt1:Paip2b: unresolved_biological_candidate_or_control
- Mx2:Slc30a7: unresolved_biological_candidate_or_control
- Myo5a:Pcid2: unresolved_biological_candidate_or_control
- Nup153:Cd74: unresolved_biological_candidate_or_control
- Osbpl8:Mcl1: unresolved_biological_candidate_or_control
- Parp12:Os9: unresolved_biological_candidate_or_control
- Pcbp2:F630028O10Rik: unresolved_biological_candidate_or_control
- Plek:Pgk1: unresolved_biological_candidate_or_control
- Pltp:Prdx1: unresolved_biological_candidate_or_control
- Pot1b:Cd37: unresolved_biological_candidate_or_control
- Ppp3ca:Gpr146: unresolved_biological_candidate_or_control
- Rab14:Gba: unresolved_biological_candidate_or_control
- Rassf3:Slfn2: unresolved_biological_candidate_or_control
- Rgs1:Zfp36: unresolved_biological_candidate_or_control
- Rplp2:Il1a: unresolved_biological_candidate_or_control
- Samd8:Thap1: unresolved_biological_candidate_or_control
- Scarf1:Gm12185: unresolved_biological_candidate_or_control
- Scpep1:Gm9774: unresolved_biological_candidate_or_control
- Sdc3:H2-D1: unresolved_biological_candidate_or_control
- Sec22b:Rnf13: unresolved_biological_candidate_or_control
- Sh3bgrl:Basp1: unresolved_biological_candidate_or_control
- Slc2a6:Bst2: unresolved_biological_candidate_or_control
- Sod2:Hk3: unresolved_biological_candidate_or_control
- Sp1:Nudt9: unresolved_biological_candidate_or_control
- Spi1:Lgmn: unresolved_biological_candidate_or_control
- Srd5a1:Ndufs6: unresolved_biological_candidate_or_control
- Stx12:Hnrnpdl: unresolved_biological_candidate_or_control
- Tle3:Zbtb37: unresolved_biological_candidate_or_control
- Tlr1:Rpl39: unresolved_biological_candidate_or_control
- Tnfaip3:Lst1: unresolved_biological_candidate_or_control
- Trim2:Gbp7: unresolved_biological_candidate_or_control
- Tyrobp:Ostc: unresolved_biological_candidate_or_control
- Ubc:Bst2: unresolved_biological_candidate_or_control
- Ube2k:Babam2: unresolved_biological_candidate_or_control
- Uqcc2:Actb: unresolved_biological_candidate_or_control
- Usp15:Qk: unresolved_biological_candidate_or_control
- Zfp36l1:Marcksl1: unresolved_biological_candidate_or_control
