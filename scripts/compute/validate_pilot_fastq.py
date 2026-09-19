"""Validate bounded real paired FASTQs and preserve count/hash evidence."""
import gzip,hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);paths=[root/'inputs'/f'SRR37513722_{mate}.fastq.gz' for mate in [1,2]]
count=0;lengths=set();first=[]
with gzip.open(paths[0],'rt') as a,gzip.open(paths[1],'rt') as b:
    while True:
        left=[a.readline().rstrip('\n') for _ in range(4)];right=[b.readline().rstrip('\n') for _ in range(4)]
        if not left[0] and not right[0]:break
        assert left[0].startswith('@') and right[0].startswith('@')
        assert left[0].split()[0].removesuffix('/1')==right[0].split()[0].removesuffix('/2')
        for read in (left,right):assert read[2].startswith('+') and len(read[1])==len(read[3]);lengths.add(len(read[1]))
        if count<3:first.append(left[0].split()[0])
        count+=1
assert count==int(sys.argv[2] if len(sys.argv)>2 else 200000)
x={'run_accession':'SRR37513722','paired_records':count,'read_lengths':sorted(lengths),'first_read_ids':first,'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
(root/'logs/fastq_validation.json').write_text(json.dumps(x,indent=2));print(json.dumps(x))
