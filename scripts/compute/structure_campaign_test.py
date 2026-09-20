"""Focused staging and real-model integrity checks; no network/GPU required."""
import argparse,csv,hashlib,tempfile,unittest
from pathlib import Path
from structure_campaign_stage import stage,validate_model
ROOT=Path(__file__).resolve().parents[2]
class CampaignChecks(unittest.TestCase):
 def create(self,root,**changes):
  seq='MPSAFEKVVKNVIKEV';sha=hashlib.sha256(seq.encode()).hexdigest();fa=root/'input.fasta';fa.write_text('>peptide_'+sha+'\n'+seq+'\n')
  row={'peptide_id':'peptide_'+sha,'sequence_sha256':sha,'role':'sensitivity','sequence_audit_passed':'true','selection_cohort':'conditional_reference','orf_assumptions':'Annotated donor start and reference transcript exon-chain reconstruction','calibration':'true','deep_dive':'false'};row.update(changes)
  selection=root/'selection.tsv'
  with selection.open('w')as f:w=csv.DictWriter(f,fieldnames=list(row),delimiter='\t');w.writeheader();w.writerow(row)
  return argparse.Namespace(selection=selection,fasta=fa,output=root/'out')
 def test_requires_explicit_conditional_assumptions(self):
  with tempfile.TemporaryDirectory()as t:
   a=self.create(Path(t),orf_assumptions='')
   with self.assertRaisesRegex(ValueError,'ORF assumptions'):stage(a)
 def test_audit_gate_and_hash_are_enforced(self):
  with tempfile.TemporaryDirectory()as t:
   a=self.create(Path(t),sequence_audit_passed='false')
   with self.assertRaisesRegex(ValueError,'audit gate'):stage(a)
   a=self.create(Path(t),sequence_sha256='bad')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):stage(a)
 def test_frozen_inputs_cannot_be_changed(self):
  with tempfile.TemporaryDirectory()as t:
   a=self.create(Path(t));stage(a);a=self.create(Path(t),calibration='false')
   with self.assertRaisesRegex(ValueError,'Frozen staging'):stage(a)
 def test_single_sequence_protocol_is_explicit_and_cannot_reuse_msa_cache(self):
  import json
  from structure_campaign_stage import import_cache
  with tempfile.TemporaryDirectory()as t:
   a=self.create(Path(t));a.msa_mode='single_sequence';stage(a)
   m=json.loads((a.output/'inputs/manifest.json').read_text());self.assertEqual(m['msa_mode'],'single_sequence');self.assertEqual(m['jobs'][0]['msa'],'empty')
   self.assertIn('single_sequence',m['jobs'][0]['job_id'])
   a.prior=Path('/unused')
   with self.assertRaisesRegex(ValueError,'cannot enter'):import_cache(a)
 def test_frozen_firstpass_export_cannot_be_overwritten(self):
  import runpy,sys
  from unittest.mock import patch
  with tempfile.TemporaryDirectory()as t:
   output=Path(t);(output/'firstpass_freeze.json').write_text('{}')
   argv=['export','--output',str(output),'--remote-base','/home/ubuntu/results/structure_campaign/compute/single_sequence_pilot']
   with patch.object(sys,'argv',argv),patch('subprocess.run',side_effect=AssertionError('Network action must not occur')):
    with self.assertRaisesRegex(RuntimeError,'Frozen first-pass'):runpy.run_path(str(ROOT/'scripts/compute/structure_campaign_export.py'),run_name='__main__')
 def test_real_cached_model_sequence_is_verified(self):
  p=ROOT/'results/structures/gsdmd_tmem106a';seq=''.join((p/'sequence.fasta').read_text().splitlines()[1:]);v=validate_model(seq,p/'model.cif',p/'plddt.npz',p/'pae.npz');self.assertEqual(v['length_aa'],118)
  with self.assertRaisesRegex(ValueError,'sequence mismatch'):validate_model('A'+seq[1:],p/'model.cif',p/'plddt.npz',p/'pae.npz')
if __name__=='__main__':unittest.main()
