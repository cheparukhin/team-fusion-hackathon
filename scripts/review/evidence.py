"""Bounded evidence tools for Codex review, with replayable input/output records.

No provisioning, API calls, shell tools or model-generated biological measurements.
The calling agent chooses a check; this module computes it from pinned artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = 'demo/data.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate(root, pair):
    data = json.loads((root / DATA).read_text())
    rows = [c for c in data['candidates'] if c['pair_id'] == pair]
    if len(rows) != 1:
        raise ValueError('Expected one exact ordered pair in the eligible panel')
    return rows[0], data


def retrieve_candidate(root, pair):
    c, _ = candidate(root, pair)
    fields = ['pair_id', 'species', 'assembly', 'annotation', 'label', 'long_read_support',
              'sample_count', 'sample_count_status', 'assay_tested', 'assay_qc_status',
              'score_rna', 'score_hic', 'hic_status', 'short_read_reported_support']
    return {**{k: c.get(k) for k in fields}, 'junctions': c['junctions'],
            'probe_junctions': c['probe_junctions'],
            'scope': 'Pair-level reported support and held-out scores; not biological truth or protein function'}, [DATA]


def compare_probe_junctions(root, pair):
    c, _ = candidate(root, pair)
    comparisons = []
    for probe in c['probe_junctions']:
        eligible = [j for j in c['junctions'] if all(j.get(k) == probe.get(k)
                    for k in ['assembly', 'chrom1', 'strand1', 'chrom2', 'strand2'])]
        offsets = [dict(read_ids=j['read_ids'], published_breakpoint1=int(j['breakpoint1']),
                        published_breakpoint2=int(j['breakpoint2']),
                        offset1=int(j['breakpoint1'])-int(probe['breakpoint1']),
                        offset2=int(j['breakpoint2'])-int(probe['breakpoint2'])) for j in eligible]
        offsets.sort(key=lambda x: (max(abs(x['offset1']), abs(x['offset2'])), x['read_ids']))
        comparisons.append({'probe_id': probe['probe_id'], 'probe_breakpoint1': int(probe['breakpoint1']),
                            'probe_breakpoint2': int(probe['breakpoint2']), 'published_offsets': offsets,
                            'closest_max_offset_nt': max(abs(offsets[0]['offset1']), abs(offsets[0]['offset2'])) if offsets else None,
                            'same_locus_and_orientation_records': len(eligible)})
    return {'pair_id': pair, 'comparisons': comparisons,
            'interpretation_limit': 'Descriptive coordinate comparison only. Published long-read coordinate conventions are not fully resolved. Small offsets may reflect convention or alignment; large offsets require source/read review. A pair-level label cannot validate every junction.'}, [DATA]


def rematch_parabricks(root, pair):
    import pandas as pd
    c, data = candidate(root, pair)
    relative = 'results/compute/pilot_2m/output/Chimeric.out.junction'
    path = root / relative
    pilot = data['nvidia_pilot']
    expected = pilot.get('artifact_sha256', {}).get(relative)
    if pilot.get('status') != 'completed' or not path.exists():
        return {'pair_id': pair, 'status': 'unavailable', 'support': None}, [DATA]
    if not expected or sha(path) != expected:
        raise ValueError('Parabricks output integrity mismatch or missing hash')
    if not c['probe_junctions']:
        return {'pair_id': pair, 'status': 'probe_coordinates_unavailable', 'support': None}, [DATA]
    if any(p['assembly'] != 'GRCm39' for p in c['probe_junctions']):
        raise ValueError('Assembly mismatch with the GRCm39 pilot')
    source = root / 'scripts/compute/match_junctions.py'
    spec = importlib.util.spec_from_file_location('review_match', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.match(pd.DataFrame(c['probe_junctions']), path.read_text().splitlines(), tolerance=10)
    reads = sorted({r['read_id'] for r in rows})
    return {'pair_id': pair, 'status': 'observed_support' if reads else 'not_detected_in_bounded_pilot',
            'support': len(reads), 'read_ids': reads, 'matches': rows, 'tolerance_nt': 10,
            'run_accession': pilot['run_accession'], 'read_pairs': pilot['read_pairs'],
            'technology': pilot['container'], 'container_digest': pilot['container_digest'],
            'gpu': pilot['gpu_name'], 'coordinate_rule': 'strand-aware exonic endpoints; direct or reverse-complement-equivalent orientation; split junctions only',
            'interpretation_limit': 'Non-detection in this deterministic prefix subsample is not a sensitivity estimate, assay failure, or evidence of biological absence.'}, [DATA, relative, 'scripts/compute/match_junctions.py']


def inspect_structure(root, pair):
    relative = 'results/structures/manifest.json'
    path = root / relative
    if not path.exists():
        return {'pair_id': pair, 'status': 'unavailable'}, []
    manifest = json.loads(path.read_text())
    assets = [a for a in manifest['assets'] if a.get('pair_id') == pair and a['structure_type'] == 'predicted']
    files = [relative]
    for asset in assets:
        structure = asset['structure_file']
        expected = next((a['sha256'] for a in manifest['artifacts'] if a['path'] == structure), None)
        if not expected or sha(root / structure) != expected:
            raise ValueError('Structure integrity mismatch or missing hash')
        files.append(structure)
    return {'pair_id': pair, 'status': 'available' if assets else 'unavailable',
            'predictions': [{k: a[k] for k in ['asset_id', 'method', 'sequence_status', 'confidence', 'interpretation', 'structure_file']} for a in assets],
            'scope': 'Manifest confidence for a sequence-verified cached prediction; no new folding run or experimental validation.'}, files


def retrieve_sources(root, pair):
    candidate(root, pair)  # reject unknown pair, but do not pretend sources are pair-specific
    relative = 'results/demo/sources/passages.json'
    return {'pair_id': pair, 'passages': json.loads((root / relative).read_text()),
            'scope': 'Fixed primary-paper passage set; only assert pair-specific findings where the text names that pair.'}, [relative]


TOOLS = {'retrieve_candidate': retrieve_candidate, 'compare_probe_junctions': compare_probe_junctions,
         'rematch_parabricks': rematch_parabricks, 'inspect_structure': inspect_structure,
         'retrieve_sources': retrieve_sources}


def execute(root, pair, tool):
    if tool not in TOOLS:
        raise ValueError('Tool is not allowed')
    started = time.monotonic()
    output, sources = TOOLS[tool](root, pair)
    return {'tool': tool, 'pair_id': pair, 'output': output,
            'sources': [{'path': p, 'sha256': sha(root / p)} for p in sources],
            'duration_seconds': round(time.monotonic() - started, 6),
            'executed_at': datetime.now(timezone.utc).isoformat()}


def record(root, run_dir, pair, tool, rationale):
    run_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(run_dir.glob('step-*.json'))
    if len(files) >= 8:
        raise ValueError('Review is bounded to eight tool calls')
    if files and json.loads(files[0].read_text())['pair_id'] != pair:
        raise ValueError('A review run must retain one ordered pair')
    if (run_dir / 'decision.json').exists():
        raise ValueError('Decision already frozen; create a new run for more checks')
    result = execute(root, pair, tool)
    result['step'] = len(files) + 1
    result['action_reason'] = rationale
    result['actor'] = 'Codex assistant in the active project task'
    result['tool_code_sha256'] = sha(Path(__file__))
    path = run_dir / f"step-{result['step']:02d}.json"
    with path.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pair', required=True)
    p.add_argument('--tool', choices=TOOLS, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--reason', required=True, help='Brief user-facing reason for choosing this check')
    a = p.parse_args()
    print(json.dumps(record(ROOT, a.run, a.pair, a.tool, a.reason), indent=2))


if __name__ == '__main__':
    main()
