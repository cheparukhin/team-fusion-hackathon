#!/usr/bin/env python3
"""Apply the RNA-only refit to published candidates outside the evaluation panel.

These exploratory scores are not external validation or newly established chRNAs.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import joblib
import numpy as np
import pandas as pd
from chrna.model import feature_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root
    panel = pd.read_csv(root / 'results/dataset_reconstruction/model_input.tsv', sep='\t')
    candidates = pd.read_csv(root / 'results/dataset_reconstruction/candidates.tsv', sep='\t')
    # Exclude every probe-panel design, including unresolved possible controls.
    eligible = candidates.exclusion_reason.fillna('').eq('') & ~candidates.in_probe_panel
    frame = candidates.loc[eligible].copy()
    bundle = joblib.load(root / 'results/classifier/model_rna.joblib')
    x = feature_frame(frame)
    frame['score_rna_refit'] = bundle['model'].predict_proba(x[bundle['features']])[:, 1]
    frame['score_status'] = 'exploratory_outside_selected_probe_panel_not_validated'
    frame['read_support_outside_training_range'] = ((frame.long_read_support < panel.long_read_support.min()) |
                                                    (frame.long_read_support > panel.long_read_support.max()))
    frame['genomic_distance_outside_training_range'] = ((frame.genomic_distance < panel.genomic_distance.min()) |
                                                        (frame.genomic_distance > panel.genomic_distance.max()))
    frame = frame.sort_values(['score_rna_refit', 'pair_id'], ascending=[False, True])
    frame['rank'] = np.arange(1, len(frame) + 1)
    frame.to_csv(root / 'results/classifier/catalogue_rankings.tsv', sep='\t', index=False)
    summary = {'ranked_pairs': len(frame), 'training_panel_pairs': len(panel),
               'excluded_from_ranking': len(candidates) - len(frame),
               'read_support_outside_training_range': int(frame.read_support_outside_training_range.sum()),
               'interpretation': 'Exploratory prioritization of already published candidates, not independent validation or new chRNA discovery.',
               'model': 'RNA-only all-panel refit; no Hi-C features available for this catalogue application.'}
    (root / 'results/classifier/catalogue_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
