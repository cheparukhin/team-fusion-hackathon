#!/usr/bin/env bash
# Executed only inside the bounded, owned CPU worker directory.
set -euo pipefail
cd /home/ubuntu/workspace/chrna-pilot
mkdir -p outputs work
exec >outputs/worker.stdout.log 2>outputs/worker.stderr.log
trap 'code=$?; printf "%s\n" "$code" > outputs/exit_code.txt; date -u +%FT%TZ > outputs/finished_utc.txt' EXIT
date -u +%FT%TZ > outputs/started_utc.txt
export PATH="$PWD/tools/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/tools/lib"
sha256sum -c inputs.sha256 > outputs/input_hash_validation.txt
sha256sum -c tools.sha256 > outputs/tool_hash_validation.txt
minimap2 --version > outputs/minimap2.version.txt
samtools --version > outputs/samtools.version.txt
uname -a > outputs/runtime.txt
lscpu >> outputs/runtime.txt
free -b >> outputs/runtime.txt
lsblk -b -o NAME,SIZE,TYPE,MOUNTPOINTS >> outputs/runtime.txt
gzip -dc inputs/gencode.vM28.annotation.gtf.gz > work/annotation.gtf
# One index (reference <4 Gbp), same splice preset and k14 as TYPHON.
/usr/bin/time -v minimap2 -x splice -k14 -I4G -t 14 -d work/genome.mmi inputs/GRCm39.primary_assembly.genome.fa.gz 2> outputs/index.log
/usr/bin/time -v bash -o pipefail -c 'minimap2 -ax splice -uf -k14 --secondary=no -G50k -t14 work/genome.mmi inputs/SRR28984805.fastq 2> outputs/alignment.log | samtools sort -n -@2 -m1G -T work/sort -o outputs/pilot.name.bam -' 2> outputs/alignment.resources.log
samtools quickcheck -v outputs/pilot.name.bam
samtools flagstat outputs/pilot.name.bam > outputs/flagstat.txt
/usr/bin/time -v LongGF outputs/pilot.name.bam work/annotation.gtf 100 50 100 2 0 1 0 > outputs/LongGF.log 2> outputs/LongGF.resources.log
# Audit every supplementary-alignment read, including proposals outside LongGF.
samtools view -f2048 outputs/pilot.name.bam | cut -f1 | sort -u > outputs/split_read_ids.txt
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('outputs')
ids = set((p/'split_read_ids.txt').read_text().splitlines())
written = 0
with open('inputs/SRR28984805.fastq') as src, (p/'split_reads.fastq').open('w') as out:
    while True:
        lines = [src.readline() for _ in range(4)]
        if not lines[0]:
            break
        if lines[0][1:].split()[0] in ids:
            out.writelines(lines)
            written += 1
assert written == len(ids), (written,len(ids))
(p/'split_read_extraction.json').write_text(json.dumps({'reads':written,'scope':'All reads with a supplementary alignment in full-sample paper-preset alignment; no published outcomes used.'},indent=2)+'\n')
PY
if test -s outputs/split_read_ids.txt; then
  /usr/bin/time -v minimap2 -ax splice -uf -k14 --MD --secondary=yes -N50 -p0.1 -G50k -t14 work/genome.mmi outputs/split_reads.fastq -o outputs/split_genome_audit.sam 2> outputs/genome_audit.log
  /usr/bin/time -v minimap2 -ax map-ont -k14 --MD --secondary=yes -N50 -p0.1 -t14 inputs/gencode.vM28.transcripts.fa.gz outputs/split_reads.fastq -o outputs/split_transcript_audit.sam 2> outputs/transcript_audit.log
else
  touch outputs/split_genome_audit.sam outputs/split_transcript_audit.sam
fi
sha256sum outputs/pilot.name.bam outputs/LongGF.log outputs/split_reads.fastq > outputs/core_output.sha256
