from pathlib import Path
import tarfile,hashlib,json,datetime
R=Path(__file__).resolve().parents[1];archive=R/'preliminary-human-cow.tar.gz'
expected=(R/'preliminary-human-cow.tar.gz.sha256').read_text().split()[0]
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
with tarfile.open(archive,'r:gz') as t:
 root='preliminary-human-cow/'
 lines=t.extractfile(root+'SHA256SUMS').read().decode().splitlines()
 for line in lines:
  digest,rel=line.split('  ',1)
  assert '..' not in Path(rel).parts
  assert hashlib.sha256(t.extractfile(root+rel).read()).hexdigest()==digest,rel
  assert hashlib.sha256((R/root/rel).read_bytes()).hexdigest()==digest,rel
result={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','archive':archive.name,'archive_sha256':expected,'verified_file_hashes':len(lines),'archive_and_extracted_files_agree':True}
(R/'qc/package_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
