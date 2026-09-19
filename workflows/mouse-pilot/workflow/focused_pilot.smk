"""Assessment and sequence stages consume preserved bounded-worker outputs.

Provisioning is explicit through scripts/run_pilot_worker.py and recorded by
its live quote/inventory, lease and shutdown artifacts. No implicit relaunch.
"""
FOCUSED = "runs/focused-pilot-20260919"
DISCOVERY = config.get("pilot_discovery_directory", FOCUSED + "/discovery")
GENOME_GZ = "data/references/gencode_M28/GRCm39.primary_assembly.genome.fa.gz"
GENOME_FA = GENOME_GZ[:-3]

rule pilot_reference_index:
    input:
        genome=GENOME_GZ,
        provenance=GENOME_GZ + ".provenance.json"
    output:
        fasta=GENOME_FA,
        index=GENOME_FA + ".fai",
        receipt=GENOME_FA + ".derivative.json"
    resources:
        mem_mb=128,
        disk_mb=3000
    shell:
        "{PYTHON:q} scripts/prepare_fasta_index.py --compressed {input.genome:q} --samtools .tools/envs/typhon/bin/samtools"

rule pilot_assessment:
    input:
        genome=DISCOVERY + "/split_genome_audit.sam",
        transcript=DISCOVERY + "/split_transcript_audit.sam",
        caller=DISCOVERY + "/LongGF.log",
        gtf="data/references/gencode_M28/gencode.vM28.annotation.gtf.gz",
        rules="docs/focused_pilot_rules.md"
    output:
        decisions=FOCUSED + "/assessment/read_decisions.json",
        ranking=FOCUSED + "/assessment/rna_ranking.json",
        unassigned=FOCUSED + "/assessment/unassigned_segments.json",
        unresolved=FOCUSED + "/assessment/unresolved_longgf_proposals.json",
        summary=FOCUSED + "/assessment/assessment_summary.json"
    params:
        directory=DISCOVERY,
        output=FOCUSED + "/assessment"
    resources:
        mem_mb=4096
    shell:
        "{PYTHON:q} -m chrna.pilot_assessment --directory {params.directory:q} --gtf {input.gtf:q} --output {params.output:q}"

rule pilot_orfs:
    input:
        rules.pilot_assessment.output,
        rules.pilot_reference_index.output,
        fastq=DISCOVERY + "/split_reads.fastq"
    output:
        FOCUSED + "/orfs/reconstructions.json",
        FOCUSED + "/orfs/protein_hypotheses.json",
        FOCUSED + "/orfs/protein_hypotheses.fasta",
        FOCUSED + "/orfs/observed_rna.fasta",
        FOCUSED + "/orfs/reference_assisted_rna.fasta",
        FOCUSED + "/orfs/orf_summary.json"
    params:
        assessment=FOCUSED + "/assessment",
        output=FOCUSED + "/orfs",
        genome=GENOME_FA
    resources:
        mem_mb=2048
    shell:
        "{PYTHON:q} -m chrna.pilot_orfs --assessment {params.assessment:q} --fastq {input.fastq:q} --genome {params.genome:q} --output {params.output:q} --limit 100"
