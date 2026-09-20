import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from compare_pairs import orthology_lookup,matches
class PairTest(unittest.TestCase):
 def test_order_and_nonhuman_anchor(self):
  rows=[{'species':'cow','gene_stable_id':a,'homology_species':'rat','homology_gene_stable_id':b,'homology_type':'ortholog_one2one','is_high_confidence':'1'} for a,b in [('C1','R1'),('C2','R2')]]
  m=orthology_lookup(rows);a={'species':'cow','gene5':'C1','gene3':'C2'};b={'species':'rat','gene5':'R1','gene3':'R2'}
  self.assertTrue(matches(a,b,m));self.assertTrue(matches(b,a,m));self.assertFalse(matches(a,dict(b,gene5='R2',gene3='R1'),m))
  rows[0]['homology_type']='ortholog_one2many';self.assertFalse(matches(a,b,orthology_lookup(rows)))
 def test_ambiguous_one_to_one_fails(self):
  rows=[{'species':'cow','gene_stable_id':'C1','homology_species':'rat','homology_gene_stable_id':b,'homology_type':'ortholog_one2one','is_high_confidence':'1'} for b in ['R1','R2']]
  with self.assertRaises(ValueError):orthology_lookup(rows)
if __name__=='__main__':unittest.main()
