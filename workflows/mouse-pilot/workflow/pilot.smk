PILOT = "runs/pilot-20260919"

rule pilot_intake:
    input:
        PILOT + "/intake_validation.json"

rule pilot_prefetch:
    input:
        config="workflow/pilot.json",
        manifest=MANIFEST
    output:
        PILOT + "/archive_receipt.json"
    shell:
        "{PYTHON:q} -m chrna.sra_stage --config {input.config:q} --stage prefetch"

rule pilot_validate:
    input:
        config="workflow/pilot.json",
        archive=rules.pilot_prefetch.output
    output:
        PILOT + "/archive_validation.json"
    shell:
        "{PYTHON:q} -m chrna.sra_stage --config {input.config:q} --stage validate"

rule pilot_extract:
    input:
        config="workflow/pilot.json",
        validated=rules.pilot_validate.output
    output:
        receipt=PILOT + "/extraction_receipt.json"
    threads: 2
    resources:
        mem_mb=2048,
        disk_mb=40000
    shell:
        "{PYTHON:q} -m chrna.sra_stage --config {input.config:q} --stage extract"

rule pilot_archive_names:
    input:
        config="workflow/pilot.json",
        validated=rules.pilot_validate.output
    output:
        receipt=PILOT + "/archive_names_receipt.json"
    shell:
        "{PYTHON:q} -m chrna.sra_stage --config {input.config:q} --stage names"

rule pilot_qc:
    input:
        config="workflow/pilot.json",
        reads=rules.pilot_extract.output,
        names=rules.pilot_archive_names.output
    output:
        PILOT + "/intake_validation.json"
    resources:
        mem_mb=1024
    shell:
        "{PYTHON:q} -m chrna.sra_stage --config {input.config:q} --stage qc"
