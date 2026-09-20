import pathlib,tempfile,unittest,subprocess,sys,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from adapt_reference import adapt,attrs
class AdapterTest(unittest.TestCase):
 def test_both_strands_coordinates_and_duplicate_symbols(self):
  with tempfile.TemporaryDirectory() as t:
   d=pathlib.Path(t);g=d/'genome.fa';gtf=d/'native.gtf';g.write_text('>1\nAAAACCCCGGGGTTTTAAAACCCCGGGGTTTT\n')
   gtf.write_text('1\tx\texon\t1\t4\t.\t+\t.\tgene_id "G1"; transcript_id "T1"; gene_name "SHARED"; transcript_biotype "protein_coding";\n1\tx\texon\t9\t12\t.\t+\t.\tgene_id "G1"; transcript_id "T1"; gene_name "SHARED";\n1\tx\texon\t17\t20\t.\t-\t.\tgene_id "G2"; transcript_id "T2"; gene_name "SHARED";\n1\tx\texon\t25\t28\t.\t-\t.\tgene_id "G2"; transcript_id "T2"; gene_name "SHARED";\nmissing\tx\texon\t1\t4\t.\t+\t.\tgene_id "G3"; transcript_id "T3";\n')
   out=d/'adapted';adapt(g,gtf,out)
   rows=[x.split('\t') for x in (out/'typhon.gtf').read_text().splitlines()]
   self.assertEqual([(x[3],x[4],x[6]) for x in rows],[('1','4','+'),('9','12','+'),('17','20','-'),('25','28','-')])
   self.assertEqual([attrs(x[8])['gene_name'] for x in rows],['G1','G1','G2','G2'])
   seq=(out/'typhon_transcripts.fa').read_text().splitlines();self.assertEqual(seq[1],'AAAAGGGG');self.assertEqual(seq[3],'CCCCTTTT')
   self.assertEqual(seq[0].split('|')[4],'G1-1');self.assertEqual(seq[0].split('|')[6],'8')
   self.assertEqual(json.loads((out/'adapter_qc.json').read_text())['excluded_contigs'],{'missing':1})
if __name__=='__main__':unittest.main()
