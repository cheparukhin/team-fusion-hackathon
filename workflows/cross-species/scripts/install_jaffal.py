"""Install JAFFA 2.3 custom tools, reuse the locked environment, apply TYPHON patches."""
import pathlib,shutil,subprocess,os,sys,urllib.request,tarfile,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];src=R/'software/JAFFA_source';dst=R/'software/jaffal/JAFFA-version-2.3'
if not dst.exists():shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.git'))
b=dst/'tools/bin';b.mkdir(parents=True,exist_ok=True)
for name in ['make_3_gene_fusion_table','extract_seq_from_fasta','make_simple_read_table','process_transcriptome_align_table']:
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++11','-O3','-o',str(b/name),str(dst/'src'/(name+'.c++'))],check=True)
u='https://github.com/ssadedin/bpipe/releases/download/0.9.9.2/bpipe-0.9.9.2.tar.gz';p=R/'software/bpipe-0.9.9.2.tar.gz'
if not p.exists():urllib.request.urlretrieve(u,p)
with tarfile.open(p) as t:
 for m in t.getmembers():
  if m.name.startswith('/') or '..' in pathlib.Path(m.name).parts:raise ValueError('Unsafe archive path')
 t.extractall(dst/'tools')
for tool in (dst/'tools/bpipe-0.9.9.2/bin').iterdir():
 link=b/tool.name
 if not link.exists():link.symlink_to(tool)
sys.path.insert(0,str(R/'software/TYPHON'));import setup_jaffal
setup_jaffal.create_tools_groovy(str(dst));setup_jaffal.apply_typhon_modifications(str(dst),1)
assert setup_jaffal.verify_jaffal_installation(str(dst))
(R/'software/jaffal_install.json').write_text(json.dumps({'JAFFA_commit':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip(),'bpipe_source':u,'bpipe_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'method':'Compile pinned JAFFA source; use locked conda tools; TYPHON create_tools_groovy and apply_typhon_modifications'},indent=2))
