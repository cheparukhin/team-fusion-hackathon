import json

import pandas as pd
import pytest

from chrna.pilot_literature import include_literature, scan_read_ids


def test_fastq_names_are_headers_not_sequence_or_comments(tmp_path):
    fastq = tmp_path / 'reads.fastq'
    fastq.write_text('@actual wanted\nACGT\n+\nIIII\n')
    result = scan_read_ids(fastq, {'wanted', 'actual'})
    assert result['records_scanned'] == 1
    assert result['matched_read_counts'] == {'actual': 1}
    fastq.write_text('@broken\nACGT\n+\nI\n')
    with pytest.raises(ValueError, match='Malformed'):
        scan_read_ids(fastq, set())


def test_absent_literature_read_is_included_but_never_supported(tmp_path):
    raw = tmp_path / 'data/raw'
    raw.mkdir(parents=True)
    pd.DataFrame([{'Read_ID': 'published', 'Chimera_ID': 'A:B', 'Gene_A': 'A', 'Gene_B': 'B'}]).to_excel(raw / 'supplementary-table-3.xlsx', index=False)
    run = tmp_path / 'run'
    (run / 'assessment').mkdir(parents=True)
    (run / 'assessment/read_decisions.json').write_text('[]')
    discovery = run / 'retry-2/worker-outputs'
    discovery.mkdir(parents=True)
    (discovery / 'split_read_ids.txt').write_text('')
    fastq = tmp_path / 'reads.fastq'
    fastq.write_text('@unrelated\nACGT\n+\nIIII\n')
    out = tmp_path / 'result'
    include_literature(tmp_path, run, fastq, ['A:B'], out)
    record = json.loads((out / 'literature_candidates.json').read_text())[0]
    assert record['included_in_literature_candidate_intake']
    assert not record['included_in_discovery_ranking']
    assert not record['pair_supported_in_pilot']
    assert record['biological_presence_in_sample'] == 'UNKNOWN'
    assert record['published_read_stage'] == 'published_read_not_in_sample'
    assert record['source_excel_row'] == 2
    with pytest.raises(FileExistsError):
        include_literature(tmp_path, run, fastq, ['A:B'], out)
    fastq.write_text('@published\nACGT\n+\nIIII\n')
    include_literature(tmp_path, run, fastq, ['A:B'], tmp_path / 'present')
    record = json.loads((tmp_path / 'present/literature_candidates.json').read_text())[0]
    assert record['published_read_stage'] == 'not_selected_for_supplementary_alignment_audit'
    assert not record['pair_supported_in_pilot']
