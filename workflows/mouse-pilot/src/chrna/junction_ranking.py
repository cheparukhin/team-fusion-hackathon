"""Deterministic RNA-only exact-junction ranking and caller deduplication.

This module consumes assessed read evidence. It neither discovers junctions nor
decides whether a transcript explains a read. No published outcomes are inputs.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import median


@dataclass(frozen=True, order=True)
class Junction:
    reference_build: str
    gene_5p: str
    chromosome_5p: str
    strand_5p: str
    boundary_5p: int
    gene_3p: str
    chromosome_3p: str
    strand_3p: str
    boundary_3p: int

    def __post_init__(self):
        if not all((self.reference_build, self.gene_5p, self.chromosome_5p, self.gene_3p, self.chromosome_3p)):
            raise ValueError("Complete reference, gene and chromosome identifiers are required")
        if self.gene_5p == self.gene_3p:
            raise ValueError("Same-gene splicing is not a two-gene junction")
        if self.strand_5p not in ("+", "-") or self.strand_3p not in ("+", "-"):
            raise ValueError("Biological strand must be explicit")
        for coordinate in (self.boundary_5p, self.boundary_3p):
            if type(coordinate) is not int or coordinate < 0:
                raise ValueError("Breakpoints are nonnegative zero-based interbase boundaries")

    @property
    def junction_id(self):
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return "junction_" + hashlib.sha256(payload.encode()).hexdigest()


STATES = {"supported_two_gene_junction": 0, "ambiguous_single_vs_split": 1,
          "insufficient_anchor": 2, "artifact_suspected": 3,
          "unmapped/unresolved": 4, "single_transcript_explained": 5}
EVIDENCE_FIELDS = {"junction", "sample_id", "biological_sample_id", "read_id", "state",
                   "mapping_specific", "split_single_margin", "shorter_anchor_nt", "caller"}
CALLERS = {"LongGF", "JAFFAL", "Genion"}
PROPOSAL_SOURCES = CALLERS | {"alignment_scan", "clip_scan"}


def aggregate_and_rank(records: list[dict]) -> list[dict]:
    """Aggregate assessed read/caller rows; stable IDs affect display order only.

    Supported rows determine support quantities. If a junction has no supported
    rows it remains in the technical-decision ledger with zero qualifying reads.
    Missing score margins stay unknown and sort after measured values. They do
    not become zero evidence or a negative biological label.
    """
    groups = defaultdict(dict)
    junctions = {}
    specimen_mapping = {}
    for record in records:
        if set(record) != EVIDENCE_FIELDS:
            raise ValueError("Ranking requires the exact RNA-evidence schema; outcomes and extra features are prohibited")
        junction = record["junction"]
        if not isinstance(junction, Junction):
            raise ValueError("An exact Junction identity is required")
        if record["state"] not in STATES:
            raise ValueError("Unknown assessed evidence state")
        if any(not isinstance(record[k], str) or not record[k] for k in ("sample_id", "biological_sample_id", "read_id", "caller")):
            raise ValueError("Sample, read and source identities must be explicit")
        if record["caller"] not in PROPOSAL_SOURCES:
            raise ValueError("Unknown proposal source")
        prior = specimen_mapping.setdefault(record["sample_id"], record["biological_sample_id"])
        if prior != record["biological_sample_id"]:
            raise ValueError("One sample cannot acquire multiple biological identities")
        if record["mapping_specific"] is not None and type(record["mapping_specific"]) is not bool:
            raise ValueError("Mapping specificity must be an assessed boolean or explicitly unknown")
        margin = record["split_single_margin"]
        if margin is not None and (isinstance(margin, bool) or not isinstance(margin, (int, float)) or not math.isfinite(margin)):
            raise ValueError("Score margin must be finite or explicitly unknown")
        anchor = record["shorter_anchor_nt"]
        if anchor is not None and (type(anchor) is not int or anchor < 0):
            raise ValueError("Anchor must be a nonnegative nucleotide count or explicitly unknown")
        jid = junction.junction_id
        junctions[jid] = junction
        # Read IDs are namespaced by specimen; agreement of callers cannot add molecules.
        key = (record["sample_id"], record["read_id"])
        base = {k: v for k, v in record.items() if k not in ("junction", "caller")}
        if key in groups[jid]:
            previous = groups[jid][key]
            if previous["evidence"] != base:
                raise ValueError("Conflicting assessment of the same molecule; reconcile upstream, not by choosing a favorable caller")
            previous["callers"].add(record["caller"])
        else:
            groups[jid][key] = {"evidence": base, "callers": {record["caller"]}}
    result = []
    for jid, reads in groups.items():
        qualifying = [r for r in reads.values() if r["evidence"]["state"] == "supported_two_gene_junction"]
        state = min((r["evidence"]["state"] for r in reads.values()), key=STATES.get)
        evidence = [r["evidence"] for r in qualifying]
        margins = [r["split_single_margin"] for r in evidence]
        # Do not make the measured subset look representative when some scores are unknown.
        score = median(margins) if margins and all(m is not None for m in margins) else None
        anchors = [r["shorter_anchor_nt"] for r in evidence]
        anchor_median = median(anchors) if anchors and all(a is not None for a in anchors) else None
        sources = set().union(*(r["callers"] for r in qualifying)) if qualifying else set()
        callers = sources & CALLERS
        counts = {s: sum(r["evidence"]["state"] == s for r in reads.values()) for s in STATES}
        row = {"junction_id": jid, **asdict(junctions[jid]), "evidence_state": state,
               "biological_samples": len({r["biological_sample_id"] for r in evidence}),
               "distinct_qualifying_reads": len(evidence),
               "mapping_specific_reads": sum(r["mapping_specific"] is True for r in evidence),
               "mapping_specificity_unknown_reads": sum(r["mapping_specific"] is None for r in evidence),
               "median_split_single_margin": score,
               "median_shorter_anchor_nt": anchor_median,
               "caller_agreement": len(callers), "callers": sorted(callers),
               "proposal_sources": sorted(sources),
               "assessed_distinct_reads": len(reads), "read_state_counts": counts}
        row["_order"] = (STATES[state], -row["biological_samples"], -len(evidence),
                         -row["mapping_specific_reads"], -(score if score is not None else -math.inf),
                         -(anchor_median if anchor_median is not None else -math.inf), -len(callers))
        result.append(row)
    result.sort(key=lambda r: (r["_order"], r["junction_id"]))
    position = 0
    while position < len(result):
        end = position + 1
        while end < len(result) and result[end]["_order"] == result[position]["_order"]:
            end += 1
        for index in range(position, end):
            result[index].update(rank_min=position + 1, rank_max=end, display_rank=index + 1)
        position = end
    for row in result:
        row.pop("_order")
    return result
