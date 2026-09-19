"""Reconstruct the separate published architecture control, never pilot recovery.

Reference-derived sequence is checked against independent published constraints;
the paper does not supply an author FASTA in the sources retrieved here.
"""
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

from chrna.pilot_orfs import IndexedFasta, revcomp, spanning_orfs


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'data/raw/published_control'
OUT = ROOT/'runs/focused-pilot-20260919/published-control'
GTF = ROOT/'data/references/gencode_M28/gencode.vM28.annotation.gtf.gz'
GENOME = ROOT/'data/references/gencode_M28/GRCm39.primary_assembly.genome.fa'


def main():
    parent = json.loads((SOURCE/'uniprot_mouse_gsdmd.json').read_text())['results'][0]
    assert parent['primaryAccession'] == 'Q9D8T2'
    parent_seq = parent['sequence']['value']
    transcripts = defaultdict(list)
    with gzip.open(GTF, 'rt') as source:
        for row, line in enumerate(source, 1):
            if 'gene_name "Gsdmd"' not in line and 'gene_name "Tmem106a"' not in line:
                continue
            f = line.rstrip().split('\t')
            if f[2] != 'exon':
                continue
            attrs = dict(re.findall(r'(\w+) "([^"]+)"', f[8]))
            exon = int(re.search(r'exon_number (\d+)', f[8])[1])
            transcripts[attrs['transcript_id']].append(dict(
                gene=attrs['gene_name'], chromosome=f[0], start=int(f[3])-1, end=int(f[4]),
                strand=f[6], exon_number=exon, source_row=row, source_line=line.rstrip()))
    genome = IndexedFasta(GENOME)
    def sequence(rows):
        return ''.join(genome.fetch(r['chromosome'], r['start'], r['end']) if r['strand']=='+'
                       else revcomp(genome.fetch(r['chromosome'], r['start'], r['end'])) for r in rows)
    candidates, accepted = [], []
    for gtid, gr in transcripts.items():
        if gr[0]['gene'] != 'Gsdmd':
            continue
        left_rows = sorted((r for r in gr if r['exon_number'] <= 2), key=lambda r:r['exon_number'])
        for ttid, tr in transcripts.items():
            if tr[0]['gene'] != 'Tmem106a' or {r['exon_number'] for r in tr} != set(range(1,10)):
                continue
            right_rows = sorted((r for r in tr if r['exon_number'] >= 6), key=lambda r:r['exon_number'])
            left, right = sequence(left_rows), sequence(right_rows)
            orfs = spanning_orfs(left+right, len(left), len(left))
            for orf in orfs:
                protein = orf['protein']
                checks = {'figure3a_length_118': len(protein)==118,
                          'figure3a_parent_first73': protein[:73]==parent_seq[:73],
                          'figure3h_tail_start_ECPEHL': protein[73:79]=='ECPEHL',
                          'methods_antibody_peptide': protein.endswith('CGRPGHQQPPPAHRPIGQ'),
                          'reported_mutation_positions': all(len(protein)>=pos and protein[pos-1]==aa for pos,aa in [(72,'E'),(74,'E'),(89,'D'),(92,'D')])}
                record = dict(parent_transcripts=[gtid,ttid], checks=checks, protein=protein,
                              rna=left+right, orf=orf, junction_offset=len(left), exon_path=left_rows+right_rows)
                candidates.append(record)
                if all(checks.values()):
                    accepted.append(record)
    assert accepted, 'No annotation reconstruction satisfies the published control constraints'
    assert len({r['protein'] for r in accepted})==1, 'Published control amino-acid sequence remains ambiguous'
    record = sorted(accepted, key=lambda r:r['parent_transcripts'])[0]
    protein = record['protein']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'published_architecture_control.fasta').write_text(
        '>published_Gsdmd_Tmem106a_control source=GENCODE_M28_reference_reconstruction NOT_pilot_recovery\n'+protein+'\n')
    (OUT/'published_architecture_control.rna.fasta').write_text(
        '>published_Gsdmd_Tmem106a_control_reference_transcript\n'+record['rna']+'\n')
    (OUT/'reconstruction_candidates.json').write_text(json.dumps(candidates,indent=2)+'\n')
    source_paths = [GTF, SOURCE/'uniprot_mouse_gsdmd.json', SOURCE/'article.html', SOURCE/'Figure3.png']
    receipt = {'created_utc':datetime.now(timezone.utc).isoformat(),
        'status':'reference_reconstruction_matching_published_constraints',
        'not_de_novo_recovered':True,'author_full_sequence_file_obtained':False,
        'protein_sha256':hashlib.sha256(protein.encode()).hexdigest(),'amino_acids':len(protein),
        'checks':record['checks'],'equivalent_parent_transcript_combinations':[r['parent_transcripts'] for r in accepted],
        'chosen_reconstruction':record,
        'source_urls':['https://www.nature.com/articles/s41586-026-10982-x',
                       'https://www.nature.com/articles/s41586-026-10982-x/figures/3',
                       'https://www.uniprot.org/uniprotkb/Q9D8T2/entry'],
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        'genome_provenance':json.loads(Path(str(GENOME)+'.derivative.json').read_text()),
        'limitation':'Reference-derived reconstruction matching published architecture, peptide and residue constraints; not an independently retrieved author full-sequence file. No author structure coordinates retrieved.'}
    (OUT/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('status','amino_acids','checks','protein_sha256')},indent=2))


if __name__=='__main__':
    main()
