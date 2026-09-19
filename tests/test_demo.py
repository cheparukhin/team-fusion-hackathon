"""Focused export/report checks: missing evidence, real scope, citations, cache binding."""
import copy,importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/demo'))
from reports import report_input,validate_report,fallback,digest
spec=importlib.util.spec_from_file_location('demo_export',ROOT/'scripts/demo/export.py');export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)

def test_report_rejects_citation_and_numeric_hallucination():
 inputs=report_input({'pair_id':'A:B','long_read_support':3},[])
 report=fallback(inputs);assert validate_report(report,inputs)
 bad=copy.deepcopy(report);bad['claims'][0]['source_ids']=['invented'];
 with pytest.raises(ValueError,match='citation'):validate_report(bad,inputs)
 bad=copy.deepcopy(report);bad['claims'][0]['text']='There are 999 reads.'
 with pytest.raises(ValueError,match='Unsupported number'):validate_report(bad,inputs)
 bad=copy.deepcopy(report);bad['numeric_claims']=[{'field':'long_read_support','value':4}]
 with pytest.raises(ValueError,match='Numeric evidence mismatch'):validate_report(bad,inputs)

def test_missing_values_and_false_flags_are_not_zero_or_truthy(tmp_path):
 p=tmp_path/'data.tsv';p.write_text('pair_id\tlong_read_support\tsample_count\tscore_rna\tshort_read_reported_support\nA:B\t0\t\t\tFalse\n')
 row=export.read_tsv(p)[0]
 assert row['long_read_support']==0
 assert row['sample_count'] is None and row['score_rna'] is None
 assert row['short_read_reported_support'] is False

def test_export_requires_real_source(tmp_path):
 with pytest.raises(ValueError,match='Real candidates'):export.build(tmp_path)

def test_exported_cohort_and_reports_are_bound_to_actual_rows():
 if not (ROOT/'demo/data.json').exists():pytest.skip('Run demo export before integration checks')
 x=json.loads((ROOT/'demo/data.json').read_text());assert not x['is_fixture']
 eligible={r['pair_id'] for r in export.read_tsv(ROOT/'results/dataset_reconstruction/model_input.tsv')}
 assert {c['pair_id'] for c in x['candidates']}==eligible
 assert all(c['sample_count'] is None for c in x['candidates'])
 authored=[c for c in x['candidates'] if c['report']['generator'].startswith('Codex')]
 assert len(authored)>=5
 for c in authored:
  inputs=report_input(c,x['sources']);report=c['report']
  assert digest(inputs)==report['provenance']['input_sha256']
  assert validate_report(report,inputs)
 assert any(c['label']==0 for c in authored) and any(c['label']==1 for c in authored)


def test_gpu_adapter_keeps_unavailable_distinct_from_observed_zero(tmp_path):
 task=tmp_path/'results/dataset_reconstruction';task.mkdir(parents=True)
 header='pair_id\tlabel\tlong_read_support\n'
 for name in ['candidates.tsv','model_input.tsv']:(task/name).write_text(header+'A:B\t0\t1\n')
 no_run=export.build(tmp_path)
 assert no_run['nvidia_pilot']['status']=='unavailable'
 assert not no_run['gpu_evidence_export_available']
 assert 'gpu_evidence' not in no_run['candidates'][0]
 compute=tmp_path/'results/compute';compute.mkdir()
 (compute/'pilot_summary.json').write_text(json.dumps({'status':'completed','read_pairs':200000}))
 (compute/'evidence.tsv').write_text('pair_id\tparabricks_support\tparabricks_status\nA:B\t0\tnot_detected_in_200000_pair_pilot\n')
 observed=export.build(tmp_path)
 assert observed['gpu_evidence_export_available']
 assert observed['candidates'][0]['gpu_evidence'][0]['parabricks_support']==0
 assert observed['candidates'][0]['label']==0
 # Independent GPU output is outside the published-evidence report inputs.
 assert digest(report_input(no_run['candidates'][0],[]))==digest(report_input(observed['candidates'][0],[]))
