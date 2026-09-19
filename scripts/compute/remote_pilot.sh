#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$HOME/chrna-rna-pilot"
mkdir -p "$TASK_ROOT"/{inputs,reference,tools,logs,output}
cd "$TASK_ROOT"
date -u +%FT%TZ > logs/start_utc.txt
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv > logs/gpu.csv
nproc > logs/cpu.txt
free -b > logs/memory.txt
df -B1 . > logs/disk.txt
IMAGE=nvcr.io/nvidia/clara/clara-parabricks:4.7.1-1
timeout 1200 docker pull "$IMAGE" > logs/docker_pull.log 2>&1 &
PULL_PID=$!
# Portable upstream tools are unpacked only inside the owned pilot directory.
curl -fL --retry 2 --max-time 600 https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.4.1/sratoolkit.3.4.1-ubuntu64.tar.gz -o tools/sratoolkit.tar.gz
mkdir -p tools/sra
tar xzf tools/sratoolkit.tar.gz -C tools/sra --strip-components=1
curl -fL --retry 2 --max-time 180 https://raw.githubusercontent.com/alexdobin/STAR/2.7.2a/bin/Linux_x86_64/STAR -o tools/STAR
chmod +x tools/STAR
./tools/STAR --version > logs/star_version.txt
./tools/sra/bin/fastq-dump --version > logs/sra_version.txt
# Deterministic first200,000 read pairs from a genuine inflammatory BMDM sample.
timeout 1800 ./tools/sra/bin/fastq-dump --split-files --gzip -N 1 -X 200000 --outdir inputs SRR37513722 > logs/fastq_dump.log 2>&1 &
FASTQ_PID=$!
# Full primary assembly and M28 annotation; no candidate-derived reference.
curl -fL --retry 2 --max-time 1200 https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M28/GRCm39.primary_assembly.genome.fa.gz -o reference/GRCm39.primary_assembly.genome.fa.gz &
FASTA_PID=$!
curl -fL --retry 2 --max-time 600 https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M28/gencode.vM28.primary_assembly.annotation.gtf.gz -o reference/gencode.vM28.primary_assembly.annotation.gtf.gz
wait "$FASTA_PID"
gzip -df reference/GRCm39.primary_assembly.genome.fa.gz
gzip -df reference/gencode.vM28.primary_assembly.annotation.gtf.gz
mkdir -p reference/star272a
timeout 2400 ./tools/STAR --runMode genomeGenerate --runThreadN 24 --genomeDir reference/star272a --genomeFastaFiles reference/GRCm39.primary_assembly.genome.fa --sjdbGTFfile reference/gencode.vM28.primary_assembly.annotation.gtf --sjdbOverhang 149 > logs/star_index.log 2>&1
wait "$FASTQ_PID"
wait "$PULL_PID"
sha256sum inputs/*.gz reference/*.fa reference/*.gtf tools/STAR tools/sratoolkit.tar.gz > logs/input_sha256.txt
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}' > logs/container_digest.json
docker run --rm --gpus all "$IMAGE" pbrun rna_fq2bam --help > logs/parabricks_help.txt 2>&1
/usr/bin/time -v timeout 1800 docker run --rm --gpus all --name chrna-rna-pilot-job -v "$TASK_ROOT":/workdir -w /workdir "$IMAGE" pbrun rna_fq2bam --in-fq /workdir/inputs/SRR37513722_1.fastq.gz /workdir/inputs/SRR37513722_2.fastq.gz --ref /workdir/reference/GRCm39.primary_assembly.genome.fa --genome-lib-dir /workdir/reference/star272a --output-dir /workdir/output --out-bam /workdir/output/SRR37513722.bam --read-files-command zcat --num-gpus 1 --sjdb-overhang 149 --min-chim-segment 15 --min-chim-overhang 15 --out-chim-type Junctions --out-chim-format 1 --no-markdups --read-group-sm SRR37513722 --read-group-pl ILLUMINA --read-group-lb GSM9569462 > logs/parabricks.log 2>&1
set +e
docker run --rm -v "$TASK_ROOT":/workdir "$IMAGE" samtools quickcheck -v /workdir/output/SRR37513722.bam > logs/bam_quickcheck.log 2>&1
QC_EXIT=$?
printf '%s\n' "$QC_EXIT" > logs/bam_quickcheck.exitcode
set -e
if [ "$QC_EXIT" -ne 0 ]; then exit "$QC_EXIT"; fi
docker run --rm -v "$TASK_ROOT":/workdir "$IMAGE" samtools flagstat /workdir/output/SRR37513722.bam > logs/bam_flagstat.txt
find output -type f -printf '%p\t%s\n' > logs/output_sizes.tsv
date -u +%FT%TZ > logs/completed_utc.txt
