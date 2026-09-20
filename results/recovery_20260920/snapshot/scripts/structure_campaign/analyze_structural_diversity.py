"""Confidence-gated, protocol-specific structural diversity from actual model files.

No inference or synthetic coordinates. Coordinates are copied unchanged from
verified source models; Foldseek compares only extracted actual domain spans.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUCCESS = {'verified', 'cached_verified'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read_tsv(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write_tsv(path, rows, fields):
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)


def domain_gate(start, end, confidence, minimum_length=50, threshold=70, required_fraction=.8):
    if not (1 <= start <= end <= len(confidence)):
        raise ValueError('domain outside the complete coordinate/confidence sequence')
    values = confidence[start - 1:end]
    if any(not math.isfinite(v) or not 0 <= v <= 100 for v in values):
        raise ValueError('invalid pLDDT value or scale')
    fraction = sum(v >= threshold for v in values) / len(values)
    reason = 'span_below_50aa' if len(values) < minimum_length else 'insufficient_local_confidence' if fraction < required_fraction else 'qualified'
    return reason, fraction


def connected_components(nodes, edges):
    parent = {n: n for n in nodes}
    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]; n = parent[n]
        return n
    for a, b in edges:
        if a not in parent or b not in parent:
            raise ValueError('edge references an unrecorded actual domain')
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    result = defaultdict(list)
    for n in sorted(nodes):
        result[find(n)].append(n)
    return list(result.values())


def expected_rarefaction(cluster_peptides, population, sample_size):
    """Expected observed cluster richness under sampling actual peptides."""
    if not 0 <= sample_size <= population:
        raise ValueError('invalid rarefaction sample size')
    if population == 0:
        return 0.0
    denominator = math.comb(population, sample_size)
    return sum(1 - (math.comb(population - len(members), sample_size) / denominator if population - len(members) >= sample_size else 0)
               for members in cluster_peptides.values())


def validate_model(job, root):
    import gemmi
    artifacts = job.get('artifacts', {})
    def artifact(name):
        raw = artifacts.get(name)
        if not raw:
            raise ValueError(f'missing_artifact:{name}')
        path = Path(raw); path = path if path.is_absolute() else root / path
        if not path.is_file():
            raise ValueError(f'unavailable_artifact:{name}')
        expected = job.get('artifact_sha256', {}).get(name)
        if expected and sha(path) != expected:
            raise ValueError(f'artifact_hash_mismatch:{name}')
        return path
    coordinate = artifact('model.cif'); confidence_file = artifact('residue_confidence.tsv')
    structure = gemmi.read_structure(str(coordinate))
    if len(structure) != 1:
        raise ValueError('model_count_not_one')
    chains = [c for c in structure[0] if any(gemmi.find_tabulated_residue(r.name).is_amino_acid() for r in c)]
    if len(chains) != 1 or chains[0].name != 'A':
        raise ValueError('expected_single_protein_chain_A')
    chain = chains[0]
    residues = [r for r in chain if gemmi.find_tabulated_residue(r.name).is_amino_acid()]
    sequence = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in residues)
    if sequence != job['sequence'] or digest(sequence) != job['sequence_sha256']:
        raise ValueError('coordinate_sequence_mismatch')
    for i, r in enumerate(residues, 1):
        if r.label_seq is not None and r.label_seq != i:
            raise ValueError('noncontiguous_label_sequence_numbering')
        if not any(a.name == 'CA' for a in r):
            raise ValueError('missing_Calpha_coordinate')
        if any(not all(math.isfinite(x) for x in [a.pos.x, a.pos.y, a.pos.z]) for a in r):
            raise ValueError('nonfinite_coordinate')
    rows = read_tsv(confidence_file)
    if len(rows) != len(sequence):
        raise ValueError('confidence_length_mismatch')
    confidence = []
    for i, (aa, row) in enumerate(zip(sequence, rows), 1):
        if int(row['residue']) != i or row['aa'] != aa or row['sequence_sha256'] != job['sequence_sha256']:
            raise ValueError('confidence_residue_identity_mismatch')
        v = float(row['plddt'])
        if not math.isfinite(v) or not 0 <= v <= 100:
            raise ValueError('confidence_scale_invalid')
        confidence.append(v)
    return structure, residues, confidence, coordinate, confidence_file


def extract_domain(residues, start, end, target):
    """Copy an actual contiguous interval, including its low-confidence residues."""
    import gemmi
    if not 1 <= start <= end <= len(residues):
        raise ValueError('domain outside coordinate sequence')
    structure = gemmi.Structure(); model = gemmi.Model('1'); chain = gemmi.Chain('A')
    for residue in residues[start - 1:end]:
        chain.add_residue(residue.clone())
    model.add_chain(chain); structure.add_model(model)
    structure.write_pdb(str(target))
    # Serialization must preserve every selected coordinate and residue identity.
    actual = gemmi.read_structure(str(target))[0]['A']
    if len(actual) != end - start + 1:
        raise ValueError('extracted_domain_residue_count_mismatch')
    for source, copied in zip(residues[start - 1:end], actual):
        if source.name != copied.name or str(source.seqid) != str(copied.seqid):
            raise ValueError('extracted_domain_residue_identity_mismatch')
        # PDB rounds coordinates to 0.001 Angstrom; retain source CIF for precision.
        for atom in source:
            matches = [a for a in copied if a.name == atom.name and a.altloc == atom.altloc]
            if len(matches) != 1 or atom.pos.dist(matches[0].pos) > .001:
                raise ValueError('extracted_coordinate_mismatch')


def run_foldseek(binary, directory, domains, protocol, work, timeout=300):
    raw = work / 'alignments.tsv'; log = work / 'foldseek.log'; work.mkdir(parents=True, exist_ok=True)
    fields = ['query', 'target', 'alntmscore', 'qcov', 'tcov', 'qlen', 'tlen', 'qstart', 'qend', 'tstart', 'tend', 'qaln', 'taln']
    cmd = [str(binary), 'easy-search', str(directory), str(directory), str(raw), str(work / 'tmp'),
           '--alignment-type', '1', '--exhaustive-search', '1', '--tmalign-fast', '0',
           '--tmscore-threshold', '0.499999', '--tmscore-threshold-mode', '0', '--cov-mode', '0', '-c', '0.8',
           '--threads', '2', '--split-memory-limit', '1G', '--max-seqs', str(max(len(domains), 300)), '-e', '1000000',
           '--format-output', ','.join(fields), '--remove-tmp-files', '1']
    (work / 'command.json').write_text(json.dumps(cmd, indent=2) + '\n')
    with log.open('w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f'Foldseek exit {result.returncode}; see {log}')
    aliases = {}
    for d in domains:
        name = d['domain_id']
        for alias in [name, name + '.pdb', name + '_A', name + '.pdb_A']:
            aliases[alias] = name
    records = []; edges = set()
    with raw.open() as f:
        for row in csv.DictReader(f, fieldnames=fields, delimiter='\t'):
            if row['query'] not in aliases or row['target'] not in aliases:
                raise ValueError('unrecognized Foldseek structure identity')
            q, t = aliases[row['query']], aliases[row['target']]
            tm, qc, tc = float(row['alntmscore']), float(row['qcov']), float(row['tcov'])
            accepted = tm >= .5 and qc >= .8 and tc >= .8
            records.append(dict(protocol_id=protocol, query_domain_id=q, target_domain_id=t, alignment_TM_score=tm,
                                query_coverage=qc, target_coverage=tc, accepted_edge=accepted, **row))
            if accepted and q != t:
                edges.add(tuple(sorted([q, t])))
    return records, sorted(edges), cmd


DOMAIN_FIELDS = ['domain_id', 'job_id', 'peptide_id', 'sequence_sha256', 'protocol_id', 'role', 'seed', 'pfam_accessions',
                 'start_residue_1based', 'end_residue_1based', 'length_aa', 'fraction_plddt_ge70', 'gate_status', 'source_coordinate',
                 'source_coordinate_sha256', 'source_confidence_sha256', 'extracted_pdb', 'extracted_pdb_sha256', 'cluster_id']
MODEL_FIELDS = ['job_id', 'peptide_id', 'sequence_sha256', 'protocol_id', 'role', 'seed', 'job_status', 'analysis_status', 'reason',
                'pfam_span_count', 'qualified_domain_count', 'qualified_residue_union_fraction']
CLUSTER_FIELDS = ['protocol_id', 'cluster_id', 'domain_id', 'peptide_id', 'job_id', 'role', 'pfam_accessions', 'domain_length_aa']


def run(root=ROOT, jobs_path=None, output=None, timeout=300):
    root = Path(root); base = root / 'results/structure_campaign'; out = Path(output) if output else base / 'diversity'
    out.mkdir(parents=True, exist_ok=True); started = time.monotonic()
    jobs_path = Path(jobs_path) if jobs_path else base / 'compute/jobs.json'
    job_bytes = jobs_path.read_bytes(); jobs = json.loads(job_bytes)
    if not isinstance(jobs, list):
        jobs = jobs['jobs']
    pfam = base / 'domains/domain_hits.tsv'; hits = read_tsv(pfam); hits_by_id = defaultdict(list)
    for h in hits:
        hits_by_id[h['sequence_id']].append(h)
    fingerprint = digest(hashlib.sha256(job_bytes).hexdigest() + sha(pfam))[:16]
    snapshot = out / 'snapshots' / fingerprint; snapshot.mkdir(parents=True, exist_ok=True)
    (snapshot / 'jobs.json').write_bytes(job_bytes)
    binary = base / 'tools/foldseek/bin/foldseek'
    if not binary.is_file():
        raise FileNotFoundError('Foldseek binary unavailable')
    version = subprocess.check_output([str(binary), 'version'], text=True).strip()
    help_text = subprocess.check_output([str(binary), 'easy-search', '-h'], text=True)
    for flag in ['--tmscore-threshold-mode', '--cov-mode', '--exhaustive-search', 'alntmscore']:
        if flag not in help_text:
            raise ValueError(f'Foldseek CLI missing required option: {flag}')
    (out / 'foldseek_easy_search_help.txt').write_text(help_text)
    # Use the prespecified first seed, even when a later seed succeeded and the
    # first failed; do not replace failures using post hoc confidence or success.
    groups = defaultdict(list)
    for j in jobs:
        groups[j['protocol_id'], j['sequence_sha256']].append(j)
    first = {min(v, key=lambda j: (int(j['seed']), j['job_id']))['job_id'] for v in groups.values()}
    model_rows = []; domain_rows = []; qualified = defaultdict(list)
    sensitivity = defaultdict(lambda: dict(peptides=set(), spans=0, available=set()))
    sensitivity_sources = []
    for job in sorted(jobs, key=lambda j: (j['protocol_id'], j['sequence_sha256'], int(j['seed']), j['job_id'])):
        protocol = job['protocol_id']; pid = job['peptide_id']
        row = dict(job_id=job['job_id'], peptide_id=pid, sequence_sha256=job['sequence_sha256'], protocol_id=protocol,
                   role=job.get('role', 'unknown'), seed=job['seed'], job_status=job['status'], analysis_status='', reason='',
                   pfam_span_count=0, qualified_domain_count=0, qualified_residue_union_fraction=0)
        if job['job_id'] not in first:
            row.update(analysis_status='not_in_first_pass_diversity', reason='additional_seed_kept_for_robustness_not_independent_diversity_unit'); model_rows.append(row); continue
        if job['status'] not in SUCCESS:
            row.update(analysis_status='model_unavailable', reason=job['status']); model_rows.append(row); continue
        try:
            structure, residues, confidence, coordinate, confidence_path = validate_model(job, root)
        except (ValueError, OSError, KeyError, RuntimeError) as error:
            row.update(analysis_status='coordinate_or_confidence_validation_failed', reason=str(error)); model_rows.append(row); continue
        spans = defaultdict(set)
        for h in hits_by_id[pid]:
            spans[int(h['sequence_start_1based']), int(h['sequence_end_1based'])].add(h['pfam_accession'])
        row['pfam_span_count'] = len(spans)
        population = 'control' if job.get('role') in {'control', 'reference_control'} else 'candidate'
        sensitivity_sources.append(dict(job_id=job['job_id'], sequence_sha256=job['sequence_sha256'],
                                        coordinate_sha256=sha(coordinate), confidence_sha256=sha(confidence_path)))
        for threshold in (60, 70, 80):
            tally = sensitivity[protocol, population, threshold]
            tally['available'].add(pid)
            passing = sum(domain_gate(lo, hi, confidence, threshold=threshold)[0] == 'qualified' for lo, hi in spans)
            tally['spans'] += passing
            if passing:
                tally['peptides'].add(pid)
        coverage = set()
        for (lo, hi), accessions in sorted(spans.items()):
            status, fraction = domain_gate(lo, hi, confidence)
            identifier = 'domain_' + digest(f'{job["job_id"]}|{lo}|{hi}')[:24]
            d = dict(domain_id=identifier, job_id=job['job_id'], peptide_id=pid, sequence_sha256=job['sequence_sha256'], protocol_id=protocol,
                     role=job.get('role', 'unknown'), seed=job['seed'], pfam_accessions=';'.join(sorted(accessions)),
                     start_residue_1based=lo, end_residue_1based=hi, length_aa=hi - lo + 1, fraction_plddt_ge70=fraction,
                     gate_status=status, source_coordinate=str(coordinate.relative_to(root)) if coordinate.is_relative_to(root) else str(coordinate),
                     source_coordinate_sha256=sha(coordinate), source_confidence_sha256=sha(confidence_path), extracted_pdb='', extracted_pdb_sha256='', cluster_id='')
            if status == 'qualified':
                folder = snapshot / digest(protocol)[:12] / 'domains'; folder.mkdir(parents=True, exist_ok=True)
                path = folder / (identifier + '.pdb')
                extract_domain(residues, lo, hi, path)
                d.update(extracted_pdb=str(path.relative_to(root)), extracted_pdb_sha256=sha(path))
                qualified[protocol].append(d); coverage.update(range(lo, hi + 1))
            domain_rows.append(d)
        row['qualified_domain_count'] = sum(d['job_id'] == job['job_id'] for d in qualified[protocol])
        row['qualified_residue_union_fraction'] = len(coverage) / len(residues)
        row['analysis_status'] = 'qualified_domain_available' if row['qualified_domain_count'] else 'unclassified_no_Pfam_GA_span' if not spans else 'unclassified_failed_domain_confidence_or_length_gate'
        model_rows.append(row)
    cluster_rows = []; alignment_rows = []; protocol_rows = []; rarefaction = []
    for protocol in sorted({j['protocol_id'] for j in jobs}):
        domains = qualified[protocol]; status = 'no_qualified_domains'; error = ''; components = []
        if len(domains) == 1:
            components = [[domains[0]['domain_id']]]; status = 'single_domain_descriptive_no_search_required'
        elif len(domains) > 1:
            folder = snapshot / digest(protocol)[:12]
            try:
                actual, edges, command = run_foldseek(binary, folder / 'domains', domains, protocol, folder / 'foldseek', timeout)
                alignment_rows.extend(actual); components = connected_components([d['domain_id'] for d in domains], edges); status = 'actual_structure_clusters_complete'
            except (RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
                status = 'foldseek_failed_or_timed_out'; error = str(exc)
        lookup = {d['domain_id']: d for d in domains}
        for component in components:
            cluster_id = 'cluster_' + digest(protocol + '|' + '|'.join(component))[:20]
            for identifier in component:
                d = lookup[identifier]; d['cluster_id'] = cluster_id
                cluster_rows.append(dict(protocol_id=protocol, cluster_id=cluster_id, domain_id=identifier, peptide_id=d['peptide_id'], job_id=d['job_id'],
                                         role=d['role'], pfam_accessions=d['pfam_accessions'], domain_length_aa=d['length_aa']))
        observed = [r for r in model_rows if r['protocol_id'] == protocol and r['analysis_status'].startswith(('qualified_', 'unclassified_'))]
        # Rarefaction is over actual modeled candidate peptides; no synthetic
        # missing structures or repeated-seed counts enter the denominator.
        candidate_ids = {r['peptide_id'] for r in observed if r['role'] not in {'control', 'reference_control'}}
        occurrences = defaultdict(set)
        for r in cluster_rows:
            if r['protocol_id'] == protocol and r['peptide_id'] in candidate_ids:
                occurrences[r['cluster_id']].add(r['peptide_id'])
        rare_status = 'too_few_actual_peptides_or_clusters_descriptive_only'
        if len(candidate_ids) >= 5 and len(occurrences) >= 2 and status == 'actual_structure_clusters_complete':
            rare_status = 'finite_observed_peptide_rarefaction_not_population_inference'
            for n in range(1, len(candidate_ids) + 1):
                rarefaction.append(dict(protocol_id=protocol, sampled_actual_peptides=n, total_actual_candidate_peptides=len(candidate_ids),
                                       expected_observed_clusters=expected_rarefaction(occurrences, len(candidate_ids), n)))
        protocol_models = [r for r in model_rows if r['protocol_id'] == protocol]
        protocol_rows.append(dict(protocol_id=protocol, status=status, error=error, planned_model_jobs=len(protocol_models),
                                  first_pass_unique_sequences=sum(r['analysis_status'] != 'not_in_first_pass_diversity' for r in protocol_models),
                                  actual_validated_first_pass_models=len(observed), unavailable_first_pass_models=sum(r['analysis_status'] == 'model_unavailable' for r in protocol_models),
                                  invalid_coordinate_or_confidence_models=sum(r['analysis_status'] == 'coordinate_or_confidence_validation_failed' for r in protocol_models),
                                  unclassified_validated_models=sum(r['analysis_status'].startswith('unclassified') for r in observed),
                                  qualified_domains=len(domains), actual_clusters=len(components) if status != 'foldseek_failed_or_timed_out' else None,
                                  candidate_peptides_in_rarefaction_denominator=len(candidate_ids), rarefaction_status=rare_status))
    sensitivity_rows = []
    for protocol in sorted({j['protocol_id'] for j in jobs}):
        for population in ('candidate', 'control'):
            planned = {j['peptide_id'] for j in jobs if j['job_id'] in first and j['protocol_id'] == protocol
                       and ('control' if j.get('role') in {'control', 'reference_control'} else 'candidate') == population}
            for threshold in (60, 70, 80):
                tally = sensitivity[protocol, population, threshold]
                sensitivity_rows.append(dict(protocol_id=protocol, population=population, residue_plddt_threshold=threshold,
                    primary_gate=threshold == 70, minimum_span_aa=50, minimum_fraction_passing=.8,
                    planned_first_pass_peptides=len(planned), actual_validated_peptide_denominator=len(tally['available']),
                    unavailable_or_invalid_peptides=len(planned) - len(tally['available']),
                    peptides_with_passing_spans=len(tally['peptides']), passing_spans=tally['spans'],
                    passing_peptide_fraction=len(tally['peptides']) / len(tally['available']) if tally['available'] else ''))
    write_tsv(out / 'gate_sensitivity.tsv', sensitivity_rows, list(sensitivity_rows[0]))
    (out / 'gate_sensitivity_provenance.json').write_text(json.dumps(dict(
        method='Actual validated first-seed coordinate/confidence identities and existing Pfam GA alignment spans; minimum50aa and80%residues passing fixed; residue pLDDT thresholds60,70,80. Only70defines primary clusters. No alternate-gate cluster inference.',
        denominator='Actual validated first-pass peptides including no-Pfam-hit peptides; planned missing/invalid peptides reported separately. Controls separate from candidates, protocols never pooled.',
        overlap='Exact duplicate intervals merged; other overlapping annotations remain explicit, not independent biological domains.',
        input_jobs_sha256=hashlib.sha256(job_bytes).hexdigest(), pfam_domain_hits_sha256=sha(pfam),
        driver_sha256=sha(Path(__file__)), sources=sensitivity_sources), indent=2) + '\n')
    write_tsv(out / 'model_audit.tsv', model_rows, MODEL_FIELDS)
    write_tsv(out / 'domain_audit.tsv', domain_rows, DOMAIN_FIELDS)
    write_tsv(out / 'clusters.tsv', cluster_rows, CLUSTER_FIELDS)
    align_fields = list(alignment_rows[0]) if alignment_rows else ['protocol_id', 'query_domain_id', 'target_domain_id', 'alignment_TM_score', 'query_coverage', 'target_coverage', 'accepted_edge']
    write_tsv(out / 'alignments.tsv', alignment_rows, align_fields)
    write_tsv(out / 'rarefaction.tsv', rarefaction, ['protocol_id', 'sampled_actual_peptides', 'total_actual_candidate_peptides', 'expected_observed_clusters'])
    summary = dict(status='computed_from_actual_available_model_snapshot', input_jobs=str(jobs_path), input_jobs_sha256=hashlib.sha256(job_bytes).hexdigest(),
                   job_snapshot=str((snapshot / 'jobs.json').relative_to(root)), input_jobs_changed_during_run=jobs_path.read_bytes() != job_bytes,
                   pfam_domain_hits_sha256=sha(pfam), driver_sha256=sha(Path(__file__)), foldseek_version=version, foldseek_binary_sha256=sha(binary),
                   protocols=protocol_rows, domain_gate=dict(minimum_contiguous_span_aa=50, minimum_residue_plddt=70, minimum_fraction_passing=.8),
                   clustering=dict(method='connected_components_of_thresholded_exhaustive_actual_domain_TMalign_edges', alignment_TM_min=.5, query_coverage_min=.8, target_coverage_min=.8,
                                   candidate_engine_threshold=.499999, note='A tiny permissive engine threshold preserves the inclusive >=0.5 post-filter; edges are rechecked from saved scores. Components may connect transitively, not all member pairs necessarily pass.'),
                   DSSP_status='unavailable_not_run' if not (shutil.which('mkdssp') or shutil.which('dssp')) else 'available_not_run_optional',
                   elapsed_seconds=time.monotonic() - started,
                   limitations=['Only actual sequence-verified coordinates are used; no synthetic result structures.', 'Protocols are never pooled for clustering.',
                                'Reference/pilot selection limits generalization; finite observed rarefaction is descriptive, not diversity of all109pairs.',
                                'No qualified span, no search hit, or singleton cluster is not evidence of a novel fold.',
                                'Whole contiguous Pfam alignment spans retained including permitted low-confidence positions; confident residues are not concatenated.',
                                'Exact duplicate Pfam spans merged; other overlapping annotations remain explicit and are not independent biological observations.',
                                'Additional seeds retained in model audit but excluded from first-pass diversity; no confidence/success-based replacement.',
                                'Only internal modeled-set clustering is performed; no external reference-fold novelty search.'])
    (out / 'METHODS.md').write_text('# Actual structure diversity\n\nEvery model must pass exact chain-A coordinate sequence/hash and residue-confidence identity checks. Source artifacts are read-only; extracted PDB domains copy all residues/atoms of contiguous Pfam spans, preserving chain and residue numbering (PDB precision0.001Å). Gate: span>=50aa and>=80%residues pLDDT>=70. No discontiguous confident-fragment concatenation. Additional seeds do not become independent diversity units.\n\nFoldseek CLI is verified against the pinned binary and [official documentation](https://github.com/steineggerlab/foldseek). Each protocol is searched separately using exhaustive TMalign, then saved alignments are filtered at alignment-normalized TM>=0.5 and coverage>=0.8 for both partners. Connected-component clusters are explicitly transitive. Pfam no-hits, domain-confidence failures, missing/failed models and clustering failures remain in audits. A singleton or no-hit is not a novel fold.\n\nFinite-set rarefaction samples actual modeled candidate peptides and counts observed thresholded clusters, accounting for multiple domains within a peptide. It is emitted only with at least5actual peptides and2observed clusters; it does not estimate unseen protein diversity or remove selection bias. Cached precomputed-MSA and single-sequence models remain separate protocols. Model-seed ensembles are outside this first-pass analysis.\n\nReproduce after collecting actual models with `.venv-disorder/bin/python scripts/structure_campaign/analyze_structural_diversity.py`. Optional `--jobs` selects a preserved actual jobs snapshot. No inference/cloud or synthetic structure generation is performed.\n')
    summary['output_sha256'] = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in {'manifest.json', 'STATUS.md'}}
    (out / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    (base / 'analysis').mkdir(exist_ok=True)
    (base / 'analysis/diversity_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'STATUS.md').write_text('# Structural diversity status\n\n' + json.dumps(protocol_rows, indent=2) + '\n')
    print(json.dumps(protocol_rows, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT); parser.add_argument('--jobs', type=Path)
    parser.add_argument('--output', type=Path); parser.add_argument('--foldseek-timeout', type=int, default=300)
    args = parser.parse_args(); run(args.root, args.jobs, args.output, args.foldseek_timeout)
