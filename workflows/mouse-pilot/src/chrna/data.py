from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

DOI = "10.1038/s41586-026-10982-x"
BASE = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10982-x/MediaObjects/"
SOURCE_FILES = {
    "supplementary-table-1.xlsx": (3, "Mouse sample metadata"),
    "supplementary-table-3.xlsx": (5, "Repaired mouse candidate read records"),
    "supplementary-table-7.xlsx": (9, "Published gene-pair confirmation lists"),
    "supplementary-table-8.xlsx": (10, "NanoString probe design sequences"),
    "supplementary-table-10.xlsx": (12, "Human sample metadata"),
}
# Reviewed aliases apply to pair-level lookup only. Original probe IDs and
# sequences are retained. A pair-level label cannot identify a positive variant.
PROBE_PAIR_ALIASES = {
    "Aoah:Sirt5_2": "Aoah:Sirt5",
    "Slc25a13:Sem1_2": "Slc25a13:Sem1",
    "Tbc1d23:Xdh_2": "Tbc1d23:Xdh",
    "Plekhm2:4930455G09Rik_2": "Plekhm2:4930455G09Rik",
    "Slc16a10:Rpf2_2": "Slc16a10:Rpf2",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_manifest(raw: Path) -> list[dict]:
    return [dict(name=name, description=desc, doi=DOI,
                 url=BASE + f"41586_2026_10982_MOESM{num}_ESM.xlsx",
                 sha256=sha256(raw / name), bytes=(raw / name).stat().st_size,
                 source_license="Study is published under CC BY 4.0; retain source attribution")
            for name, (num, desc) in SOURCE_FILES.items()]


def fetch(root: Path) -> None:
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for name, (num, _) in SOURCE_FILES.items():
        path = raw / name
        if not path.exists():
            url = BASE + f"41586_2026_10982_MOESM{num}_ESM.xlsx"
            with urlopen(url, timeout=90) as response:
                payload = response.read(25_000_001)
            if len(payload) > 25_000_000 or not payload.startswith(b"PK"):
                raise ValueError(f"Invalid or unexpectedly large XLSX: {name}")
            path.write_bytes(payload)
    manifest_path = root / "data/sources.json"
    manifest = source_manifest(raw)
    if manifest_path.exists():
        original = {x["name"]: x["sha256"] for x in json.loads(manifest_path.read_text())}
        for source in manifest:
            if source["name"] in original and source["sha256"] != original[source["name"]]:
                raise ValueError(f"Source changed: {source['name']}; review before updating the pinned manifest")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def assign_components(frame: pd.DataFrame, probes: pd.DataFrame, folds: int = 5) -> pd.DataFrame:
    """Group shared parental genes and identical probe sequences without outcomes."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a, b):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)

    for row in frame.itertuples():
        union(row.gene_a, row.gene_b)
    for _, group in probes.groupby("sequence_sha256"):
        pairs = group.pair_id.tolist()
        for pair in pairs[1:]:
            union(pairs[0].split(":")[0], pair.split(":")[0])
    result = frame[["pair_id", "gene_a", "gene_b"]].copy()
    result["component"] = [find(gene) for gene in result.gene_a]
    sizes = result.groupby("component").size().to_dict()
    assignment, loads = {}, [0] * folds
    for component in sorted(sizes, key=lambda g: (-sizes[g], g)):
        fold = min(range(folds), key=lambda f: (loads[f], f))
        assignment[component] = fold
        loads[fold] += sizes[component]
    result["fold"] = result.component.map(assignment)
    result["partition"] = np.where(result.fold == folds - 1, "heldout", "development")
    return result


def build(root: Path) -> dict:
    fetch(root)
    raw, out, reports = root / "data/raw", root / "data/processed", root / "reports"
    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(exist_ok=True)
    reads = pd.read_excel(raw / "supplementary-table-3.xlsx")
    validation = pd.read_excel(raw / "supplementary-table-7.xlsx")
    probes = pd.read_excel(raw / "supplementary-table-8.xlsx")
    if reads.Read_ID.isna().any() or reads.Read_ID.duplicated().any():
        raise ValueError("Read records must have unique, non-missing IDs")
    probes = probes.rename(columns={"Chimera_Probe_ID": "probe_id", "Plate": "plate",
                                    "Junction_sequence_used_for_probe_design": "sequence"})
    probes["source_excel_row"] = np.arange(2, len(probes) + 2)
    probes["pair_id"] = probes.probe_id.map(lambda x: PROBE_PAIR_ALIASES.get(x, x))
    probes["sequence"] = probes.sequence.str.upper()
    if not probes.sequence.str.fullmatch("[ACGT]+").all() or probes.probe_id.duplicated().any():
        raise ValueError("Invalid probe sequence or duplicate probe ID")
    probes["sequence_sha256"] = probes.sequence.map(lambda s: hashlib.sha256(s.encode()).hexdigest())
    probes["sequence_origin"] = "published_probe_design_not_raw_read"
    probes["junction_offset"] = pd.NA  # Table 8 does not explicitly provide offsets.
    probes["probe_variant_confirmation"] = "not_provided_at_probe_variant_level"

    long_support = reads.groupby("Chimera_ID").Read_ID.nunique()
    junction_columns = ["Chromosome_Gene_A", "Breakpoint_Coordinate_Gene_A", "Strand_Gene_A",
                        "Chromosome_Gene_B", "Breakpoint_Coordinate_Gene_B", "Strand_Gene_B"]
    junctions = reads.groupby(["Chimera_ID"] + junction_columns, dropna=False).agg(
        supporting_read_count=("Read_ID", "nunique")).reset_index()
    junction_count = junctions.groupby("Chimera_ID").size()
    nano = set(validation.nCounter_NanoString_Validated.dropna())
    short = set(validation.Short_Read_RNA_Sequencing_Validated.dropna())
    both = set(validation["Cross-validated"].dropna())
    if both != nano & short:
        raise ValueError("Published overlap column does not match the intersection of lists")
    if not nano <= set(probes.pair_id):
        raise ValueError("Some confirmed pairs cannot be matched to probe design records")

    pairs = pd.DataFrame({"pair_id": sorted(set(probes.pair_id))})
    genes = pairs.pair_id.str.split(":", expand=True)
    if genes.shape[1] != 2:
        raise ValueError("Unexpected ordered gene-pair syntax")
    pairs["gene_a"], pairs["gene_b"] = genes[0], genes[1]
    pairs["probe_count"] = pairs.pair_id.map(probes.groupby("pair_id").size())
    pairs["long_read_support"] = pairs.pair_id.map(long_support)
    pairs["repaired_junction_count"] = pairs.pair_id.map(junction_count)
    pairs["catalogue_match"] = "exact_ordered_pair"
    missing = pairs.long_read_support.isna()
    reverse = (pairs.gene_b + ":" + pairs.gene_a).isin(long_support.index)
    pairs.loc[missing & reverse, "catalogue_match"] = "reverse_name_only_unresolved_junction"
    pairs.loc[missing & ~reverse, "catalogue_match"] = "not_found_in_table_3"
    # Unknown support remains missing, not zero; only exact matches enter
    # the common baseline pool. No reverse-pair merger is performed.
    pairs["baseline_eligible"] = ~missing
    pairs["short_read_reported_support"] = pairs.pair_id.isin(short)
    pairs["sequence_available"] = True
    pairs["sequence_variant_ambiguous"] = pairs.probe_count > 1
    pairs["species"] = "Mus musculus"
    pairs["genome_build"] = "GRCm39"
    pairs["biological_context"] = "mouse_BMDM_multiple_states_aggregated"
    pairs["sample_level_support_available"] = False
    pairs["mean_probe_gc_fraction"] = pairs.pair_id.map(
        probes.assign(gc=probes.sequence.str.count("[GC]") / probes.sequence.str.len()).groupby("pair_id").gc.mean())
    first = reads.drop_duplicates("Chimera_ID").set_index("Chimera_ID")
    pairs["chromosomal_status"] = pairs.pair_id.map(first.Chromosomal_Status)
    distances = (first.Breakpoint_Coordinate_Gene_A - first.Breakpoint_Coordinate_Gene_B).abs()
    distances = distances.where(first.Chromosome_Gene_A == first.Chromosome_Gene_B)
    pairs["intrachromosomal_distance_bp"] = pairs.pair_id.map(distances)
    pairs.loc[pairs.repaired_junction_count > 1, "intrachromosomal_distance_bp"] = np.nan

    outcomes = pairs[["pair_id"]].copy()
    outcomes["nanostring_reported_support"] = outcomes.pair_id.isin(nano)
    outcomes["rna_evidence_status"] = np.where(outcomes.nanostring_reported_support,
                                               "reported_nanostring_support", "unconfirmed")
    outcomes["biological_negative_label"] = pd.NA
    outcomes["assay_failure_or_nondetection"] = "not_recoverable_from_confirmation_list"
    outcomes["label_scope"] = "ordered_gene_pair_across_study_not_specific_probe_or_sample"
    outcomes["protein_evidence"] = np.where(outcomes.pair_id == "Gsdmd:Tmem106a",
                                            "detailed_functional_validation_in_paper", "not_assessed_here")
    splits = assign_components(pairs, probes)
    pairs = pairs.merge(splits[["pair_id", "component", "fold", "partition"]], on="pair_id", validate="one_to_one")

    pairs.to_csv(out / "candidate_pairs.csv", index=False)
    probes.to_csv(out / "probe_sequences.csv", index=False)
    outcomes.to_csv(out / "evaluation_outcomes.csv", index=False)
    junctions.to_csv(out / "catalogue_junctions.csv", index=False)
    splits.to_csv(out / "splits.csv", index=False)
    pairs.loc[~pairs.baseline_eligible].to_csv(out / "unresolved_catalogue_matches.csv", index=False)
    with (out / "probe_sequences.fasta").open("w") as stream:
        for row in probes.itertuples():
            stream.write(f">{row.probe_id}\n{row.sequence}\n")
    findings = {
        "study_doi": DOI,
        "catalogue_read_records": int(len(reads)),
        "catalogue_gene_pairs": int(reads.Chimera_ID.nunique()),
        "catalogue_repaired_junctions": int(len(junctions)),
        "probe_records": int(len(probes)), "probe_gene_pairs": int(len(pairs)),
        "nanostring_supported_gene_pairs": len(nano),
        "short_read_supported_gene_pairs_full_study": len(short),
        "both_supported_gene_pairs_full_study": len(both),
        "exact_catalogue_matches": int(pairs.baseline_eligible.sum()),
        "catalogue_match_counts": {str(k): int(v) for k, v in pairs.catalogue_match.value_counts().items()},
        "multi_probe_pairs": pairs.loc[pairs.probe_count > 1, "pair_id"].tolist(),
        "reviewed_probe_aliases": PROBE_PAIR_ALIASES,
        "probe_sequence_lengths": sorted(map(int, probes.sequence.str.len().unique())),
        "known_true_negatives": 0,
        "supervised_biological_classifier_ready": False,
        "label_grain": "gene pair; exact-junction, probe-variant and sample labels unavailable",
        "partition_counts": {str(k): int(v) for k, v in pairs.partition.value_counts().items()},
        "gene_components": int(splits.component.nunique()),
        "largest_gene_component": int(splits.groupby("component").size().max()),
        "limitations": [
            "No full NanoString assay/QC outcomes; not-reported is unknown, not false.",
            "Probe panel was selected by the original authors, not a random sample of all candidates.",
            "Gene-pair confirmation cannot resolve multiple probes or exact transcript junctions.",
            "Reference-derived probe windows are not observed raw-read sequences.",
            "Read counts aggregate the whole mouse study; no specimen mapping is in Table 3.",
            "Unresolved catalogue names are excluded from common-pool ranking, not declared false.",
            "RNA support is not protein production or function."
        ],
    }
    (reports / "data_audit.json").write_text(json.dumps(findings, indent=2) + "\n")
    return findings
