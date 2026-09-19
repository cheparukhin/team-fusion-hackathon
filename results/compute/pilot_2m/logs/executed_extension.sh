#!/usr/bin/env bash
# Optional single larger run, only after 200k pilot finds no panel matches.
set -euo pipefail
TASK_BASE="$HOME/chrna-rna-pilot"
TASK_ROOT="$HOME/chrna-rna-pilot-2m"
mkdir -p "$TASK_ROOT"/{inputs,logs,output}
cd "$TASK_ROOT"
date -u +%FT%TZ > logs/start_utc.txt
IMAGE=nvcr.io/nvidia/clara/clara-parabricks:4.7.1-1
timeout 1200 "$TASK_BASE/tools/sra/bin/fastq-dump" --split-files --gzip -N 1 -X 2000000 --outdir inputs SRR37513722 > logs/fastq_dump.log 2>&1
sha256sum inputs/*.gz > logs/input_sha256.txt
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}' > logs/container_digest.json
/usr/bin/time -v timeout 1200 docker run --rm --gpus all --name chrna-rna-extension-job -v "$TASK_ROOT":/workdir -v "$TASK_BASE/reference":/reference:ro -w /workdir "$IMAGE" pbrun rna_fq2bam --in-fq /workdir/inputs/SRR37513722_1.fastq.gz /workdir/inputs/SRR37513722_2.fastq.gz --ref /reference/GRCm39.primary_assembly.genome.fa --genome-lib-dir /reference/star272a --output-dir /workdir/output --out-bam /workdir/output/SRR37513722.bam --read-files-command zcat --num-gpus 1 --sjdb-overhang 149 --min-chim-segment 15 --min-chim-overhang 15 --out-chim-type Junctions --out-chim-format 1 --no-markdups --read-group-sm SRR37513722 --read-group-pl ILLUMINA --read-group-lb GSM9569462 > logs/parabricks.log 2>&1
set +e
docker run --rm -v "$TASK_ROOT":/workdir "$IMAGE" samtools quickcheck -v /workdir/output/SRR37513722.bam > logs/bam_quickcheck.log 2>&1
QC_EXIT=$?
printf '%s\n' "$QC_EXIT" > logs/bam_quickcheck.exitcode
set -e
if [ "$QC_EXIT" -ne 0 ]; then exit "$QC_EXIT"; fi
docker run --rm -v "$TASK_ROOT":/workdir "$IMAGE" samtools flagstat /workdir/output/SRR37513722.bam > logs/bam_flagstat.txt
find output -type f -printf '%p\t%s\n' > logs/output_sizes.tsv
date -u +%FT%TZ > logs/completed_utc.txt

