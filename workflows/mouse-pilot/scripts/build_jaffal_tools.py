"""Compile JAFFAL's four local utilities using an explicitly supplied compiler."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    names = ["extract_seq_from_fasta", "make_simple_read_table", "process_transcriptome_align_table", "make_3_gene_fusion_table"]
    results = []
    for name in names:
        source = args.source / "src" / (name + ".c++")
        target = args.source / "tools/bin" / name
        argv = [str(args.compiler), "-std=c++11", "-O3", "-o", str(target), str(source)]
        subprocess.run(argv, check=True)
        results.append({"name": name, "source_sha256": digest(source), "binary_sha256": digest(target), "argv": argv})
    args.report.write_text(json.dumps({"status": "compiled", "tools": results,
                                       "limitation": "Compilation is not a validated JAFFAL analysis."}, indent=2) + "\n")


if __name__ == "__main__":
    main()
