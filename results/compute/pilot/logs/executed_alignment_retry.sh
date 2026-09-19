#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$HOME/chrna-rna-pilot"
cd "$TASK_ROOT"
IMAGE=nvcr.io/nvidia/clara/clara-parabricks:4.7.1-1
mv logs/parabricks.log logs/parabricks_initial_parameter_failure.log
mv output output_initial_parameter_failure
mkdir output
cp reference/star272a/genomeParameters.txt logs/genomeParameters.txt
cp Log.out logs/star_index_details.log
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

