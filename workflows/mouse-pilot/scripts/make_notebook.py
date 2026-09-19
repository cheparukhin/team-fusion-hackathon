"""Build and optionally execute a portable notebook using the project pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def create():
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    notebook = nbf.v4.new_notebook(cells=[
        md("# Chimeric RNA evidence audit and baseline benchmark\n\n"
           "This pilot asks whether simple rankings recover published independent RNA support within a selected probe panel. "
           "The source is [Venezia et al., Nature (2026)](https://doi.org/10.1038/s41586-026-10982-x). "
           "It does not predict protein existence or biological function."),
        md("## Findings\n\nThe 529 probe sequences represent 527 ordered gene pairs. "
           "109 pairs are listed as NanoString-supported. There are **no established biological negatives**. "
           "Only 479 panel pairs exactly match the main read catalogue. The comparison below uses the development partition; "
           "the reserved held-out partition is not evaluated."),
        md("## Methods and assumptions\n\nThe initial evaluation unit is an **ordered gene pair**, because the published "
           "confirmation list does not identify particular probe variants, reads or samples. "
           "Unreported support remains unknown. We keep shared parental genes and duplicate sequences in the same split, "
           "compare methods on one eligible pool, and average ties analytically. The interval columns describe tie-breaking "
           "variability, not confidence about biological truth."),
        code("from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display, Image\n"
             "from chrna.data import build\nfrom chrna.benchmark import benchmark, plot\n"
             "root = Path.cwd()\nif not (root / 'pyproject.toml').exists():\n    root = root.parent\n"
             "assert (root / 'pyproject.toml').exists(), 'Run from the repository or notebooks directory'\n"
             "pd.set_option('display.max_colwidth', 75)"),
        md("## Sources and data quality\n\nOriginal spreadsheet downloads are checksum-pinned. "
           "The feature table and evaluation outcomes are separate files. Raw sequencing reads are not required for this pilot."),
        code("audit = build(root)\nsummary_keys = ['catalogue_read_records', 'catalogue_gene_pairs', "
             "'probe_records', 'probe_gene_pairs', 'nanostring_supported_gene_pairs', 'exact_catalogue_matches', 'known_true_negatives']\n"
             "display(pd.DataFrame({'Quantity': summary_keys, 'Count': [audit[k] for k in summary_keys]}))"),
        code("sources = pd.read_json(root / 'data/sources.json')\n"
             "display(sources[['name', 'description', 'sha256']])"),
        md("### Name matching and probe variants\n\nA missing match is never converted to zero support. "
           "Reverse-name matches require junction verification. The two pairs with multiple probes remain one pair each in the benchmark."),
        code("display(pd.DataFrame(audit['catalogue_match_counts'].items(), columns=['Match status', 'Pairs']))\n"
             "print('Pairs with multiple probes:', ', '.join(audit['multi_probe_pairs']))\n"
             "candidates = pd.read_csv(root / 'data/processed/candidate_pairs.csv')\n"
             "display(candidates.loc[~candidates.baseline_eligible, ['pair_id','catalogue_match']].head(8))"),
        md("### Split integrity\n\nConnected components are formed from parental genes and identical sequences without outcome labels. "
           "Fold 4 is reserved. These splits do not eliminate all protein/gene-family homology."),
        code("display(candidates.groupby(['partition','fold']).agg(Pairs=('pair_id','size'), "
             "Eligible_pairs=('baseline_eligible','sum')).reset_index())\n"
             "splits = pd.read_csv(root / 'data/processed/splits.csv')\n"
             "genes_by_fold = {fold: set(g.gene_a) | set(g.gene_b) for fold, g in splits.groupby('fold')}\n"
             "assert all(not genes_by_fold[a] & genes_by_fold[b] for a in genes_by_fold for b in genes_by_fold if a < b)\n"
             "print('Verified: no parental gene crosses folds.')"),
        md("## Development results\n\nThe fixed baselines use no NanoString outcome to calculate scores. "
           "Reported short-read support is an additional assay-derived comparator, not a sequence-only prediction. "
           "All three methods receive the same eligible development pool."),
        code("results = benchmark(root, partition='development')\n"
             "display(results[['method','k','expected_supported_at_k','known_positive_recall_at_k',"
             "'tie_breaking_lower_95','tie_breaking_upper_95']].round(3))"),
        code("figure_path = plot(root, partition='development')\ndisplay(Image(filename=str(figure_path)))"),
        md("## Interpretation and next experiment\n\nRead-based evidence already provides a meaningful baseline. "
           "Any sequence model should demonstrate added value over these methods. "
           "Most read-count scores are tied, so a single convenient ordering would be misleading. "
           "Before fitting a biological classifier, obtain suitable negative/assay-QC evidence or define and disclose a different estimand. "
           "Frozen RNA embeddings can be generated independently of these outcomes, but they are not yet part of this result.\n\n"
           "The panel was selected by the original researchers. Recovery of its published support does not establish precision in "
           "unselected historical datasets. Exact-junction matching and an external study remain necessary extensions."),
        code("import importlib.metadata as metadata\n"
             "display(pd.DataFrame({'Package': ['chrna-prioritization','numpy','pandas','scipy','matplotlib'], "
             "'Version': [metadata.version(x) for x in ['chrna-prioritization','numpy','pandas','scipy','matplotlib']]}))")
    ])
    notebook.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    notebook.metadata.language_info = {"name": "python", "version": sys.version.split()[0]}
    nbf.validate(notebook)
    return notebook


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    notebook = create()
    if args.execute:
        from nbclient import NotebookClient
        from jupyter_client import KernelManager
        from jupyter_client.kernelspec import KernelSpecManager
        import json
        cache = ROOT / '.cache/kernels/python3'
        cache.mkdir(parents=True, exist_ok=True)
        (cache / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Project Python', 'language': 'python'}))
        manager = KernelManager(kernel_name='python3',
                                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(cache.parent)]))
        NotebookClient(notebook, timeout=240, km=manager,
                       resources={'metadata': {'path': str(ROOT)}}).execute()
    destination = ROOT / 'notebooks/01_data_audit_and_baselines.ipynb'
    destination.parent.mkdir(exist_ok=True)
    nbf.write(notebook, destination)
    if args.execute:
        from nbconvert import HTMLExporter
        body, _ = HTMLExporter(template_name='lab').from_notebook_node(notebook)
        (ROOT / 'reports/notebook.html').write_text(body)
    print(destination)


if __name__ == '__main__':
    main()
