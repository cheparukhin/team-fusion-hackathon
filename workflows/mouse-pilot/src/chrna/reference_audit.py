"""Streaming reference identity and annotation-coverage checks."""
from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .references import file_hashes


def fasta_lengths(path: Path, gencode: bool = False) -> dict[str, int]:
    opener = gzip.open if path.suffix == ".gz" else open
    lengths = {}
    current = None
    with opener(path, "rt") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                current = line[1:].split()[0]
                if gencode:
                    current = current.split("|")[0]
                if current in lengths:
                    raise ValueError(f"Duplicate FASTA ID: {current}")
                lengths[current] = 0
            elif current is None:
                raise ValueError("FASTA sequence before header")
            else:
                if re.search(r"[^ACGTRYSWKMBDHVNacgtryswkmbdhvn]", line):
                    raise ValueError(f"Invalid nucleotide symbol: {current}")
                lengths[current] += len(line)
    if not lengths or any(length == 0 for length in lengths.values()):
        raise ValueError("Empty reference sequence")
    return lengths


def audit(genome: Path, gtf: Path, transcriptome: Path) -> dict:
    contigs = fasta_lengths(genome)
    sequences = fasta_lengths(transcriptome, gencode=True)
    transcript_types = {}
    exon_lengths: dict[str, int] = defaultdict(int)
    absent_contigs: Counter = Counter()
    invalid_intervals = []
    transcript_contigs = {}
    opener = gzip.open if gtf.suffix == ".gz" else open
    with opener(gtf, "rt") as handle:
        for row_number, line in enumerate(handle, 1):
            if line.startswith("#") or not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9:
                raise ValueError(f"Malformed GTF row {row_number}")
            chrom, _, feature, start, end, _, strand, _, attributes = fields
            start, end = int(start), int(end)
            if chrom not in contigs:
                absent_contigs[chrom] += 1
            elif start < 1 or end < start or end > contigs[chrom]:
                invalid_intervals.append(row_number)
            attrs = dict(re.findall(r'(\w+) "([^"]*)";', attributes))
            transcript = attrs.get("transcript_id")
            if feature == "transcript":
                if not transcript or transcript in transcript_types:
                    raise ValueError(f"Missing or duplicate transcript ID at row {row_number}")
                transcript_types[transcript] = attrs.get("transcript_type", "UNKNOWN")
                transcript_contigs[transcript] = chrom
            elif feature == "exon":
                if not transcript:
                    raise ValueError(f"Exon without transcript at row {row_number}")
                exon_lengths[transcript] += end - start + 1
    missing = sorted(set(transcript_types) - sequences.keys())
    extra = sorted(sequences.keys() - transcript_types.keys())
    mismatches = [{"transcript_id": t, "exon_bases": exon_lengths.get(t, 0), "fasta_bases": sequences[t]}
                  for t in sorted(transcript_types.keys() & sequences.keys())
                  if exon_lengths.get(t, 0) != sequences[t]]
    types = dict(sorted(Counter(transcript_types.values()).items()))
    has_noncoding = any(t in types for t in ("lncRNA", "lincRNA", "antisense", "processed_transcript"))
    result = {"genome_contigs": len(contigs), "genome_bases": sum(contigs.values()),
              "annotation_transcripts": len(transcript_types), "fasta_transcripts": len(sequences),
              "transcript_biotypes": types, "noncoding_transcripts_present": has_noncoding,
              "annotation_contigs_absent_from_genome": dict(absent_contigs),
              "invalid_gtf_coordinate_rows": invalid_intervals,
              "annotation_transcripts_missing_from_fasta": missing,
              "fasta_transcripts_absent_from_annotation": extra,
              "exon_length_discrepancies": mismatches,
              "limitation": "Checks identities, coordinate bounds and lengths; does not verify every exon nucleotide against the genome."}
    result["compatible_for_alignment"] = bool(transcript_types) and has_noncoding and not any(
        (absent_contigs, invalid_intervals, missing, extra, mismatches))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    names = ["GRCm39.primary_assembly.genome.fa.gz", "gencode.vM28.annotation.gtf.gz", "gencode.vM28.transcripts.fa.gz"]
    receipts = {}
    for name in names:
        path = args.directory / name
        receipt = json.loads(Path(str(path) + ".provenance.json").read_text())
        md5, sha = file_hashes(path)
        if (md5, sha) != (receipt["md5"], receipt["sha256"]):
            raise ValueError(f"Reference changed since transfer: {name}")
        receipts[name] = receipt
    result = audit(*(args.directory / name for name in names))
    result["references"] = receipts
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("references", "exon_length_discrepancies")}))


if __name__ == "__main__":
    main()
