"""Local Pfam GA-threshold search over conditional peptides and parent controls.

No sequence upload. Stream small batches of profiles against an in-memory
sequence database; never load the complete Pfam profile collection into RAM.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import itertools
import json
import resource
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read_tsv(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f, delimiter='\t'))


def fasta(path):
    sequences = {}; name = None
    with Path(path).open() as f:
        for line in f:
            if line.startswith('>'):
                name = line[1:].split()[0]
                if name in sequences:
                    raise ValueError(f'duplicate FASTA identifier: {name}')
                sequences[name] = ''
            elif line.strip():
                if name is None:
                    raise ValueError('sequence before FASTA identifier')
                sequences[name] += line.strip().upper()
    return sequences


def write_tsv(path, rows, fields):
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)


def text(x):
    return x.decode() if isinstance(x, bytes) else str(x)


def checked_interval(start, end, length):
    """Validate an inclusive, one-based aligned span before reporting coverage."""
    if not (1 <= start <= end <= length):
        raise ValueError(f'invalid interval [{start},{end}] for length {length}')
    return start, end


def merged_length(intervals):
    end = 0; total = 0
    for lo, hi in sorted(intervals):
        if lo < 1 or hi < lo:
            raise ValueError('invalid one-based interval')
        total += max(0, hi - max(end, lo - 1))
        end = max(end, hi)
    return total


def retained_mapping(candidate, parent, links, domain_start, domain_end):
    """Map only exact, contiguous canonical parent segments; no novel-tail transfer."""
    checked_interval(domain_start, domain_end, len(parent))
    retained = []; candidate_intervals = []
    for link in links:
        ps, pe = int(link['parent_residue_start_1based']), int(link['parent_residue_end_1based'])
        cs, ce = int(link['candidate_residue_start_1based']), int(link['candidate_residue_end_1based'])
        checked_interval(ps, pe, len(parent)); checked_interval(cs, ce, len(candidate))
        if pe - ps != ce - cs or parent[ps - 1:pe] != candidate[cs - 1:ce]:
            raise ValueError('retained parent segment does not match candidate amino acids')
        lo, hi = max(ps, domain_start), min(pe, domain_end)
        if lo <= hi:
            retained.append((lo, hi)); candidate_intervals.append((cs + lo - ps, cs + hi - ps))
    return merged_length(retained) / (domain_end - domain_start + 1), candidate_intervals


HIT_FIELDS = ['sequence_id', 'role', 'sequence_sha256', 'length_aa', 'pfam_accession', 'pfam_name', 'description',
              'hmm_length', 'hmm_start_1based', 'hmm_end_1based', 'hmm_coverage', 'sequence_start_1based', 'sequence_end_1based',
              'envelope_start_1based', 'envelope_end_1based', 'sequence_span_coverage', 'sequence_bitscore', 'domain_bitscore',
              'sequence_evalue', 'domain_independent_evalue', 'domain_conditional_evalue', 'sequence_GA_bitscore', 'domain_GA_bitscore', 'domain_number']
RETENTION_FIELDS = ['orf_id', 'peptide_id', 'parent_transcript_id', 'parent_control_id', 'pfam_accession', 'pfam_name',
                    'parent_domain_start_1based', 'parent_domain_end_1based', 'parent_domain_hmm_coverage', 'retained_aligned_span_fraction',
                    'candidate_intervals_1based_inclusive', 'retention_status', 'interpretation']


def run(root=ROOT, output=None, cpus=2, batch_size=32):
    import pyhmmer
    if cpus < 1 or cpus > 2 or batch_size < 1 or batch_size > 64:
        raise ValueError('bounded scan requires 1–2 CPUs and 1–64 profiles per batch')
    root = Path(root); base = root / 'results/structure_campaign'
    out = Path(output) if output else base / 'domains'; out.mkdir(parents=True, exist_ok=True)
    cohort = base / 'cohort'; control_dir = base / 'analysis/controls'
    hmm_path = base / 'reference/pfam/Pfam-A.hmm.gz'; release_path = base / 'reference/pfam/relnotes.txt'
    if 'RELEASE 38.2' not in release_path.read_text():
        raise ValueError('expected pinned Pfam release 38.2')
    inputs = [hmm_path, release_path, cohort / 'peptides.tsv', cohort / 'conditional_peptides.fasta', cohort / 'orf_hypotheses.tsv',
              cohort / 'control_links.tsv', control_dir / 'metadata.tsv', control_dir / 'sequences.fasta']
    input_hashes = {str(p.relative_to(root)): sha(p) for p in inputs}
    candidates = [r for r in read_tsv(cohort / 'peptides.tsv') if r['conditional_census_eligible'] == 'True']
    controls = [r for r in read_tsv(control_dir / 'metadata.tsv') if r['sequence_analysis_eligible'] == 'True']
    cfasta = fasta(cohort / 'conditional_peptides.fasta'); pfasta = fasta(control_dir / 'sequences.fasta')
    sequences = {}; metadata = {}
    for role, records, seqs, key in [('conditional_candidate', candidates, cfasta, 'peptide_id'), ('parent_control', controls, pfasta, 'control_id')]:
        assert {r[key] for r in records} == set(seqs), role
        for r in records:
            name = r[key]; seq = seqs[name]
            if seq != r['sequence'] or len(seq) != int(r['length_aa']) or hashlib.sha256(seq.encode()).hexdigest() != r['sequence_sha256']:
                raise ValueError(f'sequence metadata mismatch: {name}')
            if name in sequences:
                raise ValueError(f'identifier collision: {name}')
            sequences[name] = seq; metadata[name] = dict(role=role, sequence_sha256=r['sequence_sha256'], length_aa=len(seq))
    alphabet = pyhmmer.easel.Alphabet.amino()
    targets = pyhmmer.easel.DigitalSequenceBlock(alphabet, [pyhmmer.easel.TextSequence(name=name, sequence=seq).digitize(alphabet) for name, seq in sequences.items()])
    results = []; profiles = 0; start = time.monotonic(); hits_by_id = defaultdict(list)
    with (out / 'alignments.jsonl').open('w') as alignment_file, gzip.open(hmm_path, 'rb') as compressed, pyhmmer.plan7.HMMFile(compressed) as hmm_file:
        while True:
            batch = list(itertools.islice(hmm_file, batch_size))
            if not batch:
                break
            for hmm, hits in zip(batch, pyhmmer.hmmsearch(batch, targets, cpus=cpus, parallel='queries', bit_cutoffs='gathering', seed=42, Z=len(targets))):
                if hmm.cutoffs.gathering is None:
                    raise ValueError('Pfam profile lacks gathering thresholds')
                seq_ga, dom_ga = hmm.cutoffs.gathering
                for hit in hits:
                    if not hit.included:
                        continue
                    name = text(hit.name); m = metadata[name]
                    for i, domain in enumerate(hit.domains, 1):
                        if not domain.included:
                            continue
                        a = domain.alignment
                        s, e = checked_interval(a.target_from, a.target_to, len(sequences[name]))
                        hs, he = checked_interval(a.hmm_from, a.hmm_to, hmm.M)
                        es, ee = checked_interval(domain.env_from, domain.env_to, len(sequences[name]))
                        if not (es <= s <= e <= ee):
                            raise ValueError('alignment extends outside domain envelope')
                        record = dict(sequence_id=name, **m, pfam_accession=text(hmm.accession), pfam_name=text(hmm.name), description=text(hmm.description),
                                      hmm_length=hmm.M, hmm_start_1based=hs, hmm_end_1based=he, hmm_coverage=(he - hs + 1) / hmm.M,
                                      sequence_start_1based=s, sequence_end_1based=e, envelope_start_1based=es, envelope_end_1based=ee,
                                      sequence_span_coverage=(e - s + 1) / len(sequences[name]), sequence_bitscore=hit.score, domain_bitscore=domain.score,
                                      sequence_evalue=hit.evalue, domain_independent_evalue=domain.i_evalue, domain_conditional_evalue=domain.c_evalue,
                                      sequence_GA_bitscore=seq_ga, domain_GA_bitscore=dom_ga, domain_number=i)
                        results.append(record); hits_by_id[name].append(record)
                        alignment_file.write(json.dumps(dict(sequence_id=name, pfam_accession=text(hmm.accession), domain_number=i,
                                                            target_start_1based=s, hmm_start_1based=hs, target_alignment=a.target_sequence, hmm_alignment=a.hmm_sequence)) + '\n')
                profiles += 1
            if profiles % 1024 == 0:
                status = dict(status='running', profiles_processed=profiles, target_sequences=len(targets), included_domain_hits=len(results), elapsed_seconds=time.monotonic() - start)
                (out / 'progress.json').write_text(json.dumps(status, indent=2) + '\n'); print(json.dumps(status), flush=True)
    results.sort(key=lambda r: (r['sequence_id'], r['sequence_start_1based'], r['sequence_end_1based'], r['pfam_accession']))
    write_tsv(out / 'domain_hits.tsv', results, HIT_FIELDS)
    architectures = []
    for name in sorted(sequences):
        hits = sorted(hits_by_id[name], key=lambda r: (r['sequence_start_1based'], r['sequence_end_1based'], r['pfam_accession']))
        intervals = [(h['sequence_start_1based'], h['sequence_end_1based']) for h in hits]
        architectures.append(dict(sequence_id=name, **metadata[name], pfam_domain_hit_count=len(hits), distinct_pfam_count=len({h['pfam_accession'] for h in hits}),
                                  aligned_residue_union_coverage=merged_length(intervals) / len(sequences[name]),
                                  architecture=';'.join(f'{h["pfam_accession"]}:{h["sequence_start_1based"]}-{h["sequence_end_1based"]}' for h in hits),
                                  domain_status='Pfam_GA_hit' if hits else 'no_Pfam_GA_hit_not_evidence_of_novel_fold',
                                  overlap_handling='all_GA_hits_retained_no_clan_competition_filter'))
    write_tsv(out / 'architectures.tsv', architectures, list(architectures[0]))
    # Full-parent hit retention is an exact amino-acid mapping, not annotation
    # transfer to a novel-frame tail or evidence that a domain remains folded.
    conditional_orfs = {r['orf_id']: r for r in read_tsv(cohort / 'orf_hypotheses.tsv') if r['annotated_donor_start'] == 'True'}
    links = read_tsv(cohort / 'control_links.tsv'); retained = defaultdict(list); full = []
    for link in links:
        if link['orf_id'] not in conditional_orfs:
            continue
        if link['control_type'] == 'retained_canonical_fragment':
            retained[link['orf_id'], link['transcript_id']].append(link)
        elif link['control_type'] == 'annotated_parent_complete_ORF':
            full.append(link)
    retention = []; seen = set(); missing_controls = set()
    for link in full:
        oid, tid, control = link['orf_id'], link['transcript_id'], link['control_id']
        if (oid, tid, control) in seen:
            continue
        seen.add((oid, tid, control)); o = conditional_orfs[oid]; pid = o['peptide_id']
        if control not in sequences:
            missing_controls.add(control); continue
        for hit in hits_by_id[control]:
            fraction, intervals = retained_mapping(sequences[pid], sequences[control], retained[oid, tid], hit['sequence_start_1based'], hit['sequence_end_1based'])
            retention.append(dict(orf_id=oid, peptide_id=pid, parent_transcript_id=tid, parent_control_id=control, pfam_accession=hit['pfam_accession'], pfam_name=hit['pfam_name'],
                                  parent_domain_start_1based=hit['sequence_start_1based'], parent_domain_end_1based=hit['sequence_end_1based'], parent_domain_hmm_coverage=hit['hmm_coverage'],
                                  retained_aligned_span_fraction=fraction, candidate_intervals_1based_inclusive=json.dumps(intervals),
                                  retention_status='at_least_90pct_parent_aligned_span' if fraction >= .9 else 'partial_parent_aligned_span' if fraction > 0 else 'no_parent_aligned_span_retained',
                                  interpretation='exact_canonical_sequence_overlap_not_domain_folding_or_function_validation'))
    write_tsv(out / 'parent_domain_retention.tsv', retention, RETENTION_FIELDS)
    elapsed = time.monotonic() - start
    summary = dict(status='complete', engine='pyhmmer.hmmsearch', pyhmmer_version=pyhmmer.__version__, pfam_release='38.2', profiles_processed=profiles,
                   candidate_sequences=len(candidates), control_sequences=len(controls), target_sequences=len(targets), included_domain_hits=len(results),
                   candidate_sequences_with_hits=sum(a['role'] == 'conditional_candidate' and a['pfam_domain_hit_count'] > 0 for a in architectures),
                   control_sequences_with_hits=sum(a['role'] == 'parent_control' and a['pfam_domain_hit_count'] > 0 for a in architectures),
                   parent_domain_retention_rows=len(retention), linked_full_parent_controls_not_in_target_inventory=len(missing_controls),
                   cpus=cpus, profile_batch_size=batch_size, elapsed_seconds=elapsed, max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   thresholds='Pfam model-specific gathering score thresholds; both hit and domain must be included', hmmsearch_Z=len(targets), seed=42,
                   coordinate_convention='all reported protein and HMM boundaries are 1-based inclusive',
                   input_sha256=input_hashes, code_sha256=sha(Path(__file__)),
                   limitations=['No sequence upload.', 'No-hit does not imply no domain, no function, or a novel fold.', 'HMM span coverage is profile-coordinate coverage, not sequence identity or proof of a complete domain.',
                                'Overlapping GA hits retained; no clan-competition filtering because no pinned clan mapping is supplied.', 'E-values use the searched small sequence database, not the number of Pfam models.',
                                'Parent retention is mapped canonical amino-acid span overlap; no out-of-frame annotation transfer.', 'All candidates remain conditional reference hypotheses, not established translated proteins.'])
    for path in inputs:
        if sha(path) != input_hashes[str(path.relative_to(root))]:
            raise RuntimeError(f'input changed during scan: {path}; results are not frozen')
    (out / 'METHODS.md').write_text('# Local Pfam domain annotation\n\nPinned Pfam 38.2 was searched with PyHMMER 0.12.3 using model-specific sequence/domain gathering thresholds. Profiles were streamed in batches of at most64 against the small target sequence database with two CPU threads; no complete in-memory Pfam profile set and no sequence upload. Domain/HMM alignment and envelope coordinates are 1-based inclusive, validated against their lengths. Both sequence and domain inclusion flags must pass. Raw domain alignments are preserved.\n\nHMM coverage is the covered profile-coordinate span divided by model length; sequence coverage is aligned target span divided by target length. Architecture coverage unions overlapping target intervals so residues are not double counted. All above-threshold domain hits are retained, including overlaps, with no clan competition filter. E-values reflect hmmsearch against this target sequence database and should not be presented as hmmscan database E-values.\n\nEvery target, including no-hit targets, has an architecture row. No hit does not establish a novel fold or absence of a domain/function. Parent-domain retention uses full-parent hits and exact amino-acid-matched canonical retained fragments per source ORF/transcript. Coverage is the fraction of the parent hit aligned span retained; >=90% is an operational annotation, not a folding or function guarantee. Novel-frame sequence is never assigned a canonical-parent domain through nucleotide provenance. Partial parent profile coverage remains explicit. Missing full-parent controls restrict retention claims.\n\nReproduce with `.venv-disorder/bin/python scripts/structure_campaign/annotate_domains.py --cpus 2`. Inputs, engine version, profile count, runtime, peak RSS and output hashes are in manifest.json.\n')
    summary['output_sha256'] = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in {'manifest.json', 'progress.json', 'STATUS.md'}}
    (out / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'progress.json').write_text(json.dumps(dict(status='complete', profiles_processed=profiles, elapsed_seconds=elapsed), indent=2) + '\n')
    (out / 'STATUS.md').write_text('# Local Pfam scan complete\n\n' + json.dumps({k: summary[k] for k in ['candidate_sequences', 'control_sequences', 'profiles_processed', 'included_domain_hits', 'elapsed_seconds', 'max_rss_kib']}, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT); parser.add_argument('--output', type=Path)
    parser.add_argument('--cpus', type=int, default=2); parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args(); run(args.root, args.output, args.cpus, args.batch_size)
