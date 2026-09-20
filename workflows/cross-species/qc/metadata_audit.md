# Sample audit

Sources: original PRJNA1188790 ENA/SRA XML and Santos-Rodriguez et al. Supplementary Dataset 1, all cached in manifest/.

| Species | Deposited liver runs | Biological samples | Primary status |
|---|---:|---:|---|
| Human | 4 | 3 | SRR31438987 and SRR31438990 are one donor, C710121 |
| Mouse | 3 | 3 | Tissue7, Tissue6, Tissue12 |
| Cow | 2 | 2 | BR-314-D1, BR-314-D2 |
| Rat | 2 | 2 provisionally reconciled by library names | Supplement read counts appear swapped between AR47/48 and AR49/50 |
| Dog | 2 | Unresolved | Conflicting tissue and donor labels; exclude from strict replicated conservation |

Dog SRR31429675 combines AR96/97; donor labels conflict between source records. SRR31429672 has an AR60 liver filename but AR60 occurs under Testis in the supplement. Expression-based tissue QC may identify an incompatible tissue, but cannot establish donor independence. No author was contacted.

Rat SRR31429701 has no ENA FASTQ link; NCBI lists 1,154,734 reads and a downloadable SRA archive. Original run XML is retained. This is availability through another endpoint, not missing biological data.

All samples are bulk tissue. Same tissue does not establish identical cell composition. Native Ensembl115 annotations are used; human-projected models from the source paper are not independent conservation evidence.

Some source libraries combined pass/fail reads. A consistent mean error-probability Phred threshold of 7 is applied and per-run input/retained read counts and IDs are recorded. This is a harmonized reanalysis threshold, not a claim to reproduce the authors' exact basecaller pass labels.
