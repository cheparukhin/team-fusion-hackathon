"""Recompute recorded evidence checks and validate decision references.

This verifies computation and source binding, not the truth of free-text reasoning.
"""
import argparse
import json
from pathlib import Path
from evidence import ROOT, execute, sha


def resolve(value, pointer):
    if not pointer.startswith('/'):
        raise ValueError('Evidence references require an absolute JSON pointer')
    for key in pointer[1:].split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validate_decision(decision, steps):
    if not steps or len(steps) > 8:
        raise ValueError('Invalid bounded trace')
    if [s['step'] for s in steps] != list(range(1, len(steps) + 1)):
        raise ValueError('Steps must be contiguous and ordered')
    if any(s['pair_id'] != decision['pair_id'] for s in steps):
        raise ValueError('Decision and evidence pair mismatch')
    if not decision.get('claims'):
        raise ValueError('Missing decision claims')
    for claim in decision['claims']:
        if claim.get('kind') not in ('observation', 'inference', 'unknown') or not claim.get('evidence'):
            raise ValueError('Claim category or evidence missing')
        for ref in claim['evidence']:
            if ref['step'] < 1 or ref['step'] > len(steps):
                raise ValueError('Unknown evidence step')
            resolve(steps[ref['step'] - 1]['output'], ref['pointer'])
    if decision['human_review']['status'] != 'pending':
        raise ValueError('Published demonstration must not fabricate completed human review')
    return True


def verify_run(root, run):
    steps = [json.loads(p.read_text()) for p in sorted(run.glob('step-*.json'))]
    decision = json.loads((run / 'decision.json').read_text())
    validate_decision(decision, steps)
    checks = []
    for step in steps:
        if step['tool_code_sha256'] != sha(root / 'scripts/review/evidence.py'):
            raise ValueError('Recorded tool implementation changed; review and record a new run')
        actual = execute(root, step['pair_id'], step['tool'])
        if actual['output'] != step['output']:
            raise ValueError(f"Evidence changed: {run.name} step {step['step']}")
        changed = [s['path'] for s in step['sources'] if not (root/s['path']).exists() or sha(root/s['path']) != s['sha256']]
        # The demo export embeds an export timestamp and other candidates/metrics.
        # Accept that file changing only when the entire relevant tool output is identical.
        if any(p != 'demo/data.json' for p in changed):
            raise ValueError(f'Pinned source changed: {changed}')
        checks.append({'step': step['step'], 'tool': step['tool'], 'output_identical': True,
                       'source_bytes_changed_but_relevant_output_identical': changed})
    return {'case': run.name, 'pair_id': decision['pair_id'], 'status': 'passed', 'checks': checks,
            'decision_sha256': sha(run / 'decision.json'),
            'step_sha256': {p.name: sha(p) for p in sorted(run.glob('step-*.json'))},
            'scope': 'Recomputed tool outputs and resolved evidence pointers. Does not automatically verify natural-language entailment or substitute for scientist review.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    runs = [a.run] if a.run else sorted(p.parent for p in (ROOT/'results/review').glob('*/decision.json'))
    if not runs:
        raise SystemExit('No completed review runs')
    report = {'status': 'passed', 'runs': [verify_run(ROOT, run) for run in runs]}
    if a.output:
        a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
