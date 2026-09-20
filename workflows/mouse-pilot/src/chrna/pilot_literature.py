"""Literature-candidate intake and read-level trace, separate from discovery ranking."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import pandas as pd


def scan_read_ids(path, wanted):
    """Scan complete FASTQ records; absence is sample-specific, never biological absence."""
    found = Counter()
    count = 0
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while header := stream.readline():
            sequence, plus, quality = (stream.readline() for _ in range(3))
            if (not header.startswith(b'@') or not plus.startswith(b'+') or
                    not sequence.strip() or len(sequence.rstrip(b'\r\n')) != len(quality.rstrip(b'\r\n'))):
                raise ValueError(f'Malformed FASTQ record {count + 1}')
            for line in (header, sequence, plus, quality):
                digest.update(line)
            name = header[1:].split()[0].decode()
            if name in wanted:
                found[name] += 1
            count += 1
    return {'records_scanned': count, 'sha256': digest.hexdigest(), 'matched_read_counts': dict(found)}


def include_literature(root, run, fastq, pairs, output):
    """Include requested published pairs without changing their sample-support status."""
    root, run, fastq, output = map(Path, (root, run, fastq, output))
    if output.exists():
        raise FileExistsError('Use a new output directory; existing audits are preserved')
    source = root / 'data/raw/supplementary-table-3.xlsx'
    table = pd.read_excel(source)
    selected = [(i + 2, r) for i, r in table.iterrows() if r['Chimera_ID'] in pairs]
    missing = set(pairs) - {r['Chimera_ID'] for _, r in selected}
    if missing:
        raise ValueError(f'Pairs absent from literature catalogue: {sorted(missing)}')
    scan = scan_read_ids(fastq, {str(r['Read_ID']) for _, r in selected})
    decisions_path = run / 'assessment/read_decisions.json'
    decisions = json.loads(decisions_path.read_text())
    split_path = run / 'retry-2/worker-outputs/split_read_ids.txt'
    split_ids = set(split_path.read_text().splitlines())
    records = []
    for source_row, r in selected:
        pair, read_id = str(r['Chimera_ID']), str(r['Read_ID'])
        read_decisions = [d for d in decisions if d['read_id'] == read_id]
        pair_decisions = [d for d in decisions if d['gene_name_5p'] + ':' + d['gene_name_3p'] == pair]
        present = read_id in scan['matched_read_counts']
        stage = ('published_read_not_in_sample' if not present else
                 'not_selected_for_supplementary_alignment_audit' if read_id not in split_ids else
                 'no_assigned_two_gene_proposal' if not read_decisions else 'assessed_see_decisions')
        records.append({'ordered_pair': pair, 'candidate_origin': 'literature',
            'included_in_literature_candidate_intake': True, 'included_in_discovery_ranking': False,
            'reference_build': 'GRCm39/GENCODE_M28', 'source_file': str(source), 'source_excel_row': source_row,
            'source_record': json.loads(r.to_json()), 'published_read_id': read_id,
            'published_read_present_in_pilot': present, 'published_read_stage': stage,
            'read_decisions': read_decisions, 'pair_decisions': pair_decisions,
            'pair_supported_in_pilot': any(d['state'] == 'supported_two_gene_junction' for d in pair_decisions),
            'exact_published_junction_recovered': 'UNKNOWN_not_established_by_pair_match',
            'biological_presence_in_sample': 'UNKNOWN', 'literature_sequence': None})
    control_path = run / 'published-control/provenance.json'
    fasta = []
    if control_path.exists():
        control = json.loads(control_path.read_text())
        reconstruction = control['chosen_reconstruction']
        # Match by recorded exon-path gene order, never by a special ranking rule.
        genes = list(dict.fromkeys(x['gene'] for x in reconstruction['exon_path']))
        pair = ':'.join(genes)
        for record in records:
            if record['ordered_pair'] == pair:
                record['literature_sequence'] = {
                    'source': 'published_architecture_reference_reconstruction',
                    'observed_in_pilot': False, 'provenance_path': str(control_path),
                    'provenance_sha256': hashlib.sha256(control_path.read_bytes()).hexdigest(),
                    'rna': reconstruction['rna'], 'protein': reconstruction['protein'],
                    'junction_offset': reconstruction['junction_offset'],
                    'parent_transcripts': reconstruction['parent_transcripts']}
        if any(r['ordered_pair'] == pair for r in records):
            fasta = [f'>{pair} origin=literature_reference_reconstruction observed_in_pilot=false\n{reconstruction["rna"]}\n']
    summary = {'status': 'literature_candidates_included_separately', 'fastq': str(fastq),
        'fastq_scan': scan, 'candidate_records': len(records),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'assessment_sha256': hashlib.sha256(decisions_path.read_bytes()).hexdigest(),
        'split_ids_sha256': hashlib.sha256(split_path.read_bytes()).hexdigest(),
        'decision_record_counts': dict(Counter(d['state'] for d in decisions)),
        'reason_counts': dict(Counter(reason for d in decisions for reason in d['reasons'])),
        'limitations': ['Decision counts are read-junction assignments, not distinct reads.',
            'Absent published read ID does not exclude other supporting reads or establish biological absence.',
            'Literature intake does not expand alignment search or constitute de novo recovery.',
            'No outcomes or literature sequences are passed to the RNA ranker; frozen results are unchanged.']}
    output.mkdir(parents=True)
    (output / 'literature_candidates.json').write_text(json.dumps(records, indent=2) + '\n')
    (output / 'literature_candidates.rna.fasta').write_text(''.join(fasta))
    (output / 'filter_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary
