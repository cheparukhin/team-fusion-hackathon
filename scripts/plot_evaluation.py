#!/usr/bin/env python3
"""Export the actual held-out comparison as PNG and SVG."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import precision_recall_curve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, default=Path('results/classifier'))
    args = parser.parse_args()
    predictions = pd.read_csv(args.results / 'predictions.tsv', sep='\t')
    metrics = json.loads((args.results / 'metrics.json').read_text())
    with_hic = metrics['matched_hic'] is not None
    frame = predictions[predictions.hic_contact_enrichment.notna()] if with_hic else predictions
    comparison = metrics['matched_hic'] if with_hic else metrics['full_panel']
    methods = [('read_support', 'score_read_support', 'Read support', '#8c969f'),
               ('rna', 'score_rna_matched' if with_hic else 'score_rna', 'RNA + genomic context', '#1b776c')]
    if with_hic:
        methods.append(('hic', 'score_hic', '+ 3D genome context', '#a457be'))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7), gridspec_kw={'width_ratios': [1.1, 1]})
    for key, score, label, color in methods:
        precision, recall, _ = precision_recall_curve(frame.label, frame[score])
        axes[0].step(recall, precision, where='post', label=label, color=color, linewidth=2)
    axes[0].axhline(frame.label.mean(), linestyle='--', color='#bbc1c7', label='Panel prevalence')
    axes[0].set(xlabel='Recall of reported support', ylabel='Precision for reported support', xlim=(0, 1), ylim=(0, 1.03))
    axes[0].legend(loc='upper right', fontsize=9, frameon=False)
    for i, (key, _, label, color) in enumerate(methods):
        ap = comparison[key]['average_precision']
        axes[1].barh(i, ap, color=color, height=.58)
        axes[1].text(ap + .015, i, f'{ap:.3f}', va='center', fontsize=11)
    axes[1].set(yticks=range(len(methods)), yticklabels=[m[2] for m in methods], xlabel='Average precision (higher is better)', xlim=(0, 1))
    axes[1].invert_yaxis()
    fig.suptitle('Can genome context prioritize independently supported chimeric RNAs?', fontsize=14, fontweight='bold', x=.04, ha='left')
    subtitle = f"Gene-disjoint held-out predictions · {len(frame)} pairs · {int(frame.label.sum())} reported positives"
    subtitle += ' · identical Hi-C-observed cohort' if with_hic else ' · spatial hypothesis not yet tested'
    fig.text(.04, .90, subtitle, fontsize=10, color='#555c63')
    footnote = 'Target: published NanoString support. Unreported does not mean biologically false. Scores are not calibrated probabilities.'
    if with_hic:
        diff = metrics['matched_hic']['comparison']
        ci = diff['ci95']
        footnote += f"\nHi-C incremental AP: {diff['delta_average_precision']:+.3f}; component-bootstrap 95% interval [{ci[0]:+.3f}, {ci[1]:+.3f}]."
    fig.text(.04, .025, footnote, fontsize=8, color='#555c63')
    fig.tight_layout(rect=[.02, .12, .99, .87])
    for extension in ['png', 'svg']:
        fig.savefig(args.results / f'evaluation.{extension}', dpi=180, facecolor='white')


if __name__ == '__main__':
    main()
