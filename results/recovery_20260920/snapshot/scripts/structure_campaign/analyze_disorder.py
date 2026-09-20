"""Reproducible sequence-disorder census; never infers translation or function."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, importlib.metadata, json, time
from pathlib import Path
import numpy as np


def read_fasta(path):
    records = {}
    key = None
    for line in Path(path).read_text().splitlines():
        if line.startswith('>'):
            key = line[1:].split()[0]
            if key in records:
                raise ValueError(f'Duplicate FASTA ID: {key}')
            records[key] = ''
        elif line.strip():
            if key is None:
                raise ValueError('Sequence before FASTA header')
            records[key] += line.strip().upper()
    for key, seq in records.items():
        if not seq or set(seq) - set('ACDEFGHIKLMNPQRSTVWY'):
            raise ValueError(f'Empty or noncanonical peptide: {key}')
    return records


def longest_run(mask):
    longest = current = 0
    for value in mask:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def summarize_scores(scores, threshold=0.5):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError('Expected nonempty finite per-residue scores')
    if np.any((scores < 0) | (scores > 1)):
        raise ValueError('Disorder scores must lie in [0,1]')
    mask = scores >= threshold
    fraction = float(mask.mean())
    return {'f_idr': fraction, 'mean_disorder_score': float(scores.mean()),
            'longest_idr': longest_run(mask),
            'predominantly_disordered': fraction > 0.5,
            'predominantly_disordered_cutoff_0_4': fraction > 0.4,
            'predominantly_disordered_cutoff_0_6': fraction > 0.6}


def region_summary(scores, start, end):
    """0-based half-open interval; missing/empty regions are unavailable, not zero."""
    if start is None or end is None:
        return None
    start, end = int(start), int(end)
    if not 0 <= start <= end <= len(scores):
        raise ValueError('Region outside peptide')
    return summarize_scores(scores[start:end]) if end > start else None


def write_tsv(path, records, fields=None):
    if fields is None:
        fields = list(dict.fromkeys(k for r in records for k in r))
    with Path(path).open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)


def analyze(fasta, metadata, out, role='candidate'):
    import metapredict as meta
    import torch
    torch.set_num_threads(2)
    start = time.monotonic()
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    sequences = read_fasta(fasta)
    records = list(csv.DictReader(Path(metadata).open(), delimiter='\t')) if metadata else []
    by_id = {r['peptide_id']: r for r in records}
    if len(by_id) != len(records):
        raise ValueError('Metadata must have exactly one row per peptide ID')
    if records and set(sequences) - set(by_id):
        raise ValueError('FASTA IDs missing from metadata')
    summaries = []; profiles = {}; domains = {}; cache = {}
    for key, sequence in sequences.items():
        digest = hashlib.sha256(sequence.encode()).hexdigest()
        if digest not in cache:
            v3 = np.asarray(meta.predict_disorder(sequence, version='V3', device='cpu', round_values=False), dtype=float)
            v1 = np.asarray(meta.predict_disorder(sequence, version='V1', device='cpu', round_values=False), dtype=float)
            segments = meta.predict_disorder_domains(sequence, version='V3')
            cache[digest] = (v3, v1, segments.disordered_domain_boundaries, segments.folded_domain_boundaries)
        v3, v1, idrs, folded = cache[digest]
        if len(v3) != len(sequence) or len(v1) != len(sequence):
            raise ValueError('Predictor/sequence length mismatch')
        record = dict(by_id.get(key, {}))
        record.update(peptide_id=key, sequence_sha256=digest, length=len(sequence), role=record.get('role') or role,
                      cohort_tier=record.get('cohort_tier') or record.get('eligibility_tier') or 'unspecified',
                      pair_ids=record.get('pair_ids') or record.get('pair_id') or '')
        record.update(summarize_scores(v3))
        v1_summary = summarize_scores(v1, threshold=0.42)
        record.update(v1_f_idr=v1_summary['f_idr'], v1_predominantly_disordered=v1_summary['predominantly_disordered'],
                      v1_v3_majority_agreement=record['predominantly_disordered'] == v1_summary['predominantly_disordered'],
                      v3_segment_f_idr=sum(b-a for a,b in idrs)/len(sequence))
        profiles[key] = {'sequence': sequence, 'metapredict_v3': v3.tolist(), 'metapredict_v1_sensitivity': v1.tolist()}
        domains[key] = {'idr_boundaries_0based_halfopen': idrs, 'non_disordered_segment_boundaries_0based_halfopen': folded,
                        'note': 'Sequence-predicted segments, not annotated protein domains or proven folded structures.'}
        summaries.append(record)
    write_tsv(out/'disorder_summary.tsv', summaries, None if summaries else ['peptide_id','cohort_tier','role','f_idr'])
    with gzip.open(out/'residue_disorder.tsv.gz', 'wt') as handle:
        writer = csv.writer(handle, delimiter='\t')
        writer.writerow(['peptide_id','pos1','aa','score','called_disordered','v1_score','v1_called_disordered'])
        for key, profile in profiles.items():
            for i,(aa,x,y) in enumerate(zip(profile['sequence'],profile['metapredict_v3'],profile['metapredict_v1_sensitivity']),1):
                writer.writerow([key,i,aa,x,int(x>=0.5),y,int(y>=0.42)])
    (out/'profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
    (out/'segments.json').write_text(json.dumps(domains,indent=2,default=lambda x:int(x))+'\n')
    groups = {}
    for row in summaries:
        group_key = f"{row['role']}:{row['cohort_tier']}"
        groups.setdefault(group_key, []).append(row)
    aggregate = {}
    for key, group in groups.items():
        aggregate[key] = {'n_peptides':len(group),'n_predominantly_disordered':sum(r['predominantly_disordered'] for r in group),
                          'fraction_predominantly_disordered':sum(r['predominantly_disordered'] for r in group)/len(group),
                          'mean_f_idr':float(np.mean([r['f_idr'] for r in group])),
                          'median_f_idr':float(np.median([r['f_idr'] for r in group])),
                          'residue_weighted_f_idr':sum(r['f_idr']*r['length'] for r in group)/sum(r['length'] for r in group),
                          'v1_fraction_predominantly_disordered':sum(r['v1_predominantly_disordered'] for r in group)/len(group),
                          'v1_v3_majority_agreement':sum(r['v1_v3_majority_agreement'] for r in group)/len(group)}
    summary = {'status':'complete','input_fasta':str(fasta),'input_fasta_sha256':hashlib.sha256(Path(fasta).read_bytes()).hexdigest(),
               'metadata_sha256':hashlib.sha256(Path(metadata).read_bytes()).hexdigest() if metadata else None,
               'n_records':len(summaries),'n_unique_sequences':len(cache),'groups':aggregate,
               'versions':{x:importlib.metadata.version(x) for x in ['metapredict','torch','numpy']},
               'method':{'primary':'metapredict V3 disorder network','residue_threshold':0.5,'comparison':'>=',
                         'protein_predominantly_disordered_threshold':0.5,'protein_comparison':'>',
                         'sensitivity':'metapredict V1, threshold >=0.42; related method, not independent validation',
                         'iupred_status':'unavailable: official download requires academic registration/license; no user identity or affiliation supplied',
                         'iupred_source':'https://iupred3.elte.hu/download_new',
                         'v3_training_caveat':'V3 training includes AlphaFold-derived information; correlation with folding confidence is not independent validation.'},
               'wall_seconds':time.monotonic()-start}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'METHODS.md').write_text('''# Sequence disorder analysis\n\nCPU metapredict 3.0.2, disorder network V3; raw normalized per-residue outputs, no predicted-pLDDT API. Residues with score >=0.5 are called disordered. f_IDR is their fraction; predominantly disordered means f_IDR >0.5, with protein-level 0.4/0.6 sensitivity. Longest IDR here is the longest consecutive run above threshold; separately saved segment calls use package defaults (minimum IDR12, minimum non-disordered segment50, gap closure10). Non-disordered segments are not experimentally established domains.\n\nV1 (residue threshold >=0.42) is a within-package sensitivity analysis, not an independent predictor. V3 training includes AlphaFold-derived information, so agreement with fold confidence is not independent validation. IUPred was not run: its official local distribution requires academic registration/license; no identity or affiliation was invented.\n\nEvery cohort tier is reported separately. Reconstructable hypothetical peptides are not demonstrated translation products. Protein-equal and residue-weighted means answer different questions. These finite-census summaries have no sampling confidence interval; predictor, ORF and ascertainment uncertainty remain. No unavailable sequence is assigned an order/disorder result.\n\nSources: https://github.com/idptools/metapredict ; https://metapredict.readthedocs.io/en/latest/usage/using-in-python.html ; https://iupred3.elte.hu/download_new\n''')
    print(json.dumps({'n_records':len(summaries),'groups':aggregate,'wall_seconds':summary['wall_seconds']},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fasta',type=Path,required=True)
    parser.add_argument('--metadata',type=Path);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--role',default='candidate');args=parser.parse_args()
    analyze(args.fasta,args.metadata,args.out,args.role)
