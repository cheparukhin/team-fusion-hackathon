"""Render a local evidence report from verified artifacts and explicit stage states."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def table(headers, rows):
    return '<table><thead><tr>' + ''.join(f'<th>{html.escape(str(h))}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'


def orf_svg(record, hypothesis):
    """Projected RNA diagram, explicitly not a full transcript/exon annotation."""
    length = len(record['reference_assisted_rna'])
    start, end = record['reference_assisted_junction_interval']
    x = lambda value: 35 + 830 * value / max(1, length)
    orf = hypothesis['orf']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 145" role="img" aria-label="Reference-assisted observed RNA path and spanning ORF">
<rect width="900" height="145" fill="white"/>
<text x="35" y="20" font-size="13">Reference-assisted RNA fragment ({length} nt); not a full-transcript assertion</text>
<rect x="35" y="40" width="{x(start)-35:.2f}" height="20" fill="#167d8d"/>
<rect x="{x(end):.2f}" y="40" width="{865-x(end):.2f}" height="20" fill="#95613b"/>
<rect x="{x(start):.2f}" y="35" width="{max(2,x(end)-x(start)):.2f}" height="30" fill="#be3c58"/>
<rect x="{x(orf['start']):.2f}" y="90" width="{x(orf['stop_start'])-x(orf['start']):.2f}" height="18" fill="#46529b"/>
<text x="35" y="130" font-size="13">ORF {orf['start']}–{orf['stop_start']} nt; junction interval {start}–{end}; protein existence UNKNOWN</text>
</svg>'''


def exon_svg(decision):
    elements=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 185" role="img" aria-label="Aligned reference blocks for both junction arms">',
              '<rect width="900" height="185" fill="white"/>',
              '<text x="35" y="18" font-size="13">Aligned reference blocks (CIGAR N gaps); each arm scaled separately, intron distances omitted</text>']
    for index,(arm,gene,color) in enumerate((('left',decision['gene_name_5p'],'#167d8d'),('right',decision['gene_name_3p'],'#95613b'))):
        a=decision[arm+'_alignment'];r=start=a['start'];blocks=[]
        for n,op in re.findall(r'(\d+)([MIDNSHP=X])',a['cigar']):
            n=int(n)
            if op in 'MD=X':r+=n
            elif op=='N':
                if r>start:blocks.append((start,r))
                r+=n;start=r
        if r>start:blocks.append((start,r))
        if a['strand']=='-':blocks.reverse()
        total=sum(end-start for start,end in blocks)
        gap=min(8,400/max(1,len(blocks)))
        available=830-gap*max(0,len(blocks)-1)
        y=60+index*75;x=35
        label=f"{gene} · {a['target']} ({a['strand']}) · read order 5′ → 3′ · {len(blocks)} blocks"
        elements.append(f'<text x="35" y="{y-13}" font-size="13">{html.escape(label)}</text>')
        for start,end in blocks:
            width=available*(end-start)/max(1,total)
            tooltip=f"{a['target']}:{start}–{end}, zero-based half-open; {end-start} nt"
            elements.append(f'<rect x="{x:.2f}" y="{y}" width="{width:.2f}" height="18" fill="{color}"><title>{html.escape(tooltip)}</title></rect>')
            x+=width+gap
        coordinate_label='; '.join(f'{start}–{end}' for start,end in blocks)
        if len(coordinate_label)>110:coordinate_label=coordinate_label[:107]+'… (full coordinates in read ledger)'
        elements.append(f'<text x="35" y="{y+36}" font-size="11">{html.escape(coordinate_label)}</text>')
    elements.append('</svg>')
    return ''.join(elements)


def render(run, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    assessment = read(run/'assessment/assessment_summary.json')
    ranking = read(run/'assessment/rna_ranking.json', [])
    decisions = read(run/'assessment/read_decisions.json', [])
    names={d['junction_id']:(d['gene_name_5p'],d['gene_name_3p']) for d in decisions}
    orfs = read(run/'orfs/orf_summary.json')
    control = read(run/'published-control/provenance.json')
    structures = read(run/'structures/summary.json')
    comparison = read(run/'published-comparison/published_comparison.json')
    flagship = read(run/'published-comparison/flagship_stage_trace.json')
    resources = read(run/'resource-accounting.json')
    metadata = read(run/'sample-metadata/verified-sample-metadata.json')
    completion = read(run/'completion-audit.json')
    freeze = read(run/'selection/freeze.json')
    selection = read(run/'selection/selection.json', {'selected': [], 'decisions': []})
    if freeze:
        for name, digest in freeze['outputs'].items():
            if hashlib.sha256((run/'selection'/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Frozen selection artifact changed: ' + name)
        ranking = read(run/'selection/rna_ranking.json')
        decisions = read(run/'selection/read_decisions.json')
        names={d['junction_id']:(d['gene_name_5p'],d['gene_name_3p']) for d in decisions}
    artifacts = output.parent/(output.stem + '_artifacts')
    artifacts.mkdir(exist_ok=True)
    def link(path, label):
        href = os.path.relpath(path, output.parent)
        return f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
    complete=bool(completion and completion.get('status')=='complete' and structures and structures['verified']==11)
    state='Focused pilot complete within the documented scope.' if complete else 'Progress snapshot; scientific deliverable unfinished.'
    sections = ['<h1>Chimeric RNA pilot — SRR28984805</h1>',
                '<p><strong>'+state+'</strong> '
                'RNA support does not demonstrate protein expression or function. '
                'Unreported support is unknown biological truth.</p>',
                f'<p>Generated {datetime.now(timezone.utc).isoformat()}. Reference: GRCm39 / GENCODE M28. '
                'One biological sample; no replication or multi-caller consensus.</p>']
    if metadata:
        sections.append('<p>Sample GSM8260877 is <strong>steady-state replicate 3</strong> of mouse bone-marrow-derived macrophages. '
                        'Inflammatory and tissue-reparative samples were not processed in this focused pilot. '
                        'The archived SRA library-selection field says “cDNA”; its construction protocol explicitly '
                        'specifies the Direct RNA Sequencing kit SQK-RNA002. Both fields are retained. '
                        '<a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE267147">GEO study and sample list</a> · '+
                        link(run/'sample-metadata/verified-sample-metadata.json','Verified sample metadata and source hash')+'</p>')
    sections.append('<h2>Stage status</h2>' + table(['Stage', 'Status'], [
        ('Input extraction and identity audit', 'Completed; 2,238,871 reads'),
        ('Biological RNA assessment', assessment['status'] if assessment else 'Pending preserved discovery outputs'),
        ('ORF reconstruction', orfs['status'] if orfs else 'Pending RNA assessment'),
        ('Protein shortlist', freeze['status'] if freeze else 'Not frozen'),
        ('Structure inference', f"{structures['verified']} verified, {structures['failed']} failed, {structures['deferred']} deferred" if structures else 'Pending local verification'),
        ('Published sequence control', control['status'] if control else 'Separate control; sequence verification pending'),
        ('Published comparison', 'Completed after freeze' if comparison is not None else 'Pending'),
    ]))
    if assessment:
        flow = [
            ('Validated input reads', 'read', 2238871),
            ('Supplementary-alignment reads assessed', 'read', assessment['assessed_split_reads']),
            ('Reads with an assigned two-gene proposal', 'read', len({d['read_id'] for d in decisions})),
            ('Reads supporting at least one exact junction', 'read', len({d['read_id'] for d in decisions if d['state']=='supported_two_gene_junction'})),
            ('All proposed exact junctions', 'junction', len(ranking)),
            ('Supported exact junctions', 'junction', sum(r['evidence_state']=='supported_two_gene_junction' for r in ranking)),
        ]
        if orfs:
            flow.append(('Supported junctions in reconstruction batch', 'junction', orfs['rna_junctions_considered']))
        if freeze:
            flow.append(('Selected distinct amino-acid sequences', 'protein hypothesis', len(selection['selected'])))
        with (artifacts/'filter_waterfall.csv').open('w', newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['stage','counting_unit','count']);writer.writerows(flow)
        sections.append('<h2>Evidence flow</h2><p>Read, junction and protein counts use different units. '
                        'Later stages do not assign biological negative labels to excluded or unresolved records.</p>' +
                        table(['Stage','Counting unit','Count'],flow) + '<p>' +
                        link(artifacts/'filter_waterfall.csv','Evidence flow (CSV)') + '</p>')
        sections.append('<h2>RNA evidence decisions</h2><p>These are technical evidence states, not biological truth labels. '
                        'Counts below are exact junctions; one read can propose multiple junctions.</p>')
        supported={r['junction_id'] for r in ranking if r['evidence_state']=='supported_two_gene_junction'}
        longgf={d['junction_id'] for d in decisions if d['junction_id'] in supported and d['proposal_source']=='LongGF'}
        sections.append(f'<p>{len(longgf)} supported exact junctions have a LongGF proposal; '
                        f'{len(supported-longgf)} come only from the supplementary-alignment scan. '
                        'The alignment scan is not an independent caller or evidence of caller consensus.</p>')
        sections.append(table(['Evidence state', 'Exact junctions'], sorted(Counter(r['evidence_state'] for r in ranking).items())))
        reasons = Counter(reason for d in decisions for reason in d['reasons'])
        sections.append('<p>Read-level reason counts overlap and must not be summed as a sequential filter waterfall.</p>' +
                        table(['Decision reason', 'Read–junction records'], sorted(reasons.items())))
        columns = list(ranking[0]) if ranking else ['junction_id', 'evidence_state']
        csvpath = artifacts/'rna_ranking.csv'
        with csvpath.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k,v in r.items()} for r in ranking)
        sections.append('<p>' + link(csvpath, 'Complete RNA ranking (CSV)') + ' · ' +
                        link(run/('selection' if freeze else 'assessment')/'read_decisions.json', 'Read decisions and alternative explanations') + ' · ' +
                        link(run/('selection/read_identity.tsv' if freeze else 'read_identity.tsv'), 'SRA aliases and original archive read names') + ' · ' +
                        link(run/'assessment/unassigned_segments.json','Unassigned segment ledger') + ' · ' +
                        link(run/'assessment/unresolved_longgf_proposals.json','Unresolved LongGF source proposals') + '</p>')
        sections.append('<h2>RNA ranking (first 100 rows)</h2>' + table(
            ['Rank interval', 'Ordered genes', 'Evidence', 'Qualifying reads', 'Single-transcript score margin'],
            [(f"{r['rank_min']}–{r['rank_max']}", ' → '.join(names.get(r['junction_id'],(r['gene_5p'],r['gene_3p']))), r['evidence_state'],
              r['distinct_qualifying_reads'], r['median_split_single_margin']) for r in ranking[:100]]))
    if freeze:
        sections.append('<h2>Protein hypotheses selected for folding</h2><p>All selected sequences are reference-assisted '
                        'hypotheses. Every selected junction has one supporting read in this sample. '
                        'Corrections and retained variants remain in the reconstruction ledger; corrected reference alleles '
                        'are assumptions, not independently observed sequence consensus. Low-quality raw RNA can have '
                        'a different ORF from its reference-assisted reconstruction.</p>')
        sections.append(table(['Order', 'Ordered genes', 'Amino acids', 'Selection reason'],
                              [(h['selection_order'], h['gene_name_5p']+' → '+h['gene_name_3p'],
                                len(h['sequence']), h['selection_reason']) for h in selection['selected']]))
        selected_csv=artifacts/'selected_candidates.csv'
        selected_columns=['selection_order','rna_rank_min','rna_rank_max','gene_name_5p','gene_name_3p',
                          'junction_id','read_id','protein_id','sequence_sha256','sequence_source','sequence',
                          'selection_reason','protein_existence','function']
        with selected_csv.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=selected_columns);writer.writeheader()
            writer.writerows({k:h[k] for k in selected_columns} for h in selection['selected'])
        sections.append('<p>' + link(run/'selection/selection.json', 'All selection and deferral decisions') + ' · ' +
                        link(selected_csv,'Selected candidate table (CSV)')+' · '+
                        link(run/'selection/selected_proteins.fasta', 'Selected protein FASTA') + ' · ' +
                        link(run/'orfs/observed_rna.fasta', 'Observed RNA FASTA') + ' · ' +
                        link(run/'orfs/reference_assisted_rna.fasta', 'Reference-assisted RNA FASTA') + ' · ' +
                        link(run/'orfs/reconstructions.json', 'Sequence corrections and reconstruction ledger') + ' · ' +
                        link(run/'selection/freeze.json', 'Freeze hashes and provenance') + '</p>')
        sections.append(table(['Selection disposition','Exact RNA junctions'],
                              sorted(Counter(d['disposition_category'] for d in selection['decisions']).items())))
        review=read(run/'selected-sequence-review.json')
        if review:
            selected_names={h['protein_id']:h['gene_name_5p']+' → '+h['gene_name_3p'] for h in selection['selected']}
            sections.append('<p>Correction counts below are ledger entries across the entire reconstructed RNA fragment, '
                            'not necessarily edits within the selected ORF. Raw-RNA ORF counts do not imply that those '
                            'ORFs match the selected reference-assisted protein.</p>'+table(
                ['Sequence','Proposal source','Whole-fragment correction/variant entries','Raw-RNA complete spanning ORFs','Translation check'],
                [(selected_names[r['protein_id']],r['source'],r['corrections_and_variants'],r['observed_complete_spanning_orfs'],
                  r['independent_translation']) for r in review['checks']]))
            sections.append('<p>'+link(run/'selected-sequence-review.json','Independent arithmetic checks and mapping review')+'</p>')
        recs = {(r['junction_id'], r['read_id']): r for r in read(run/'orfs/reconstructions.json', [])}
        by_read={(d['junction_id'],d['read_id']):d for d in decisions if d['state']=='supported_two_gene_junction'}
        for h in selection['selected']:
            r = recs[(h['junction_id'], h['read_id'])]
            diagram = artifacts/(h['protein_id'] + '.svg')
            diagram.write_text(orf_svg(r, h))
            exons=artifacts/(h['protein_id']+'_alignment_blocks.svg')
            exons.write_text(exon_svg(by_read[(h['junction_id'],h['read_id'])]))
            sections.append('<p>' + link(diagram, h['gene_name_5p']+' → '+h['gene_name_3p']+' RNA/ORF diagram') + ' · ' +
                            link(exons,'Aligned blocks and coordinates') + '</p>' + exons.read_text() + orf_svg(r, h))
    if control:
        sections.append('<h2>Separate published architecture control</h2><p>The 118-residue reference reconstruction '
                        'matches the published parental segment, novel-tail motif, antibody peptide and specified residue positions. '
                        'It is not de novo pilot recovery, and an author-provided full-sequence file has not been retrieved. '
                        '<a href="https://www.nature.com/articles/s41586-026-10982-x/figures/3">Published Figure 3</a>; '
                        '<a href="https://www.uniprot.org/uniprotkb/Q9D8T2/entry">parental UniProt record</a>.</p><p>' +
                        link(run/'published-control/provenance.json', 'Control reconstruction checks and reference provenance') + ' · ' +
                        link(run/'published-control/published_architecture_control.fasta', 'Separate control protein FASTA') + '</p>')
    if comparison is not None:
        supported_rows=[r for r in comparison if r['rna_evidence_state']=='supported_two_gene_junction']
        selected_ids={h['junction_id'] for h in selection['selected']}
        selected_rows=[r for r in comparison if r['junction_id'] in selected_ids]
        sections.append('<h2>Post-freeze published evidence comparison</h2><p>This join was performed after freezing RNA ranking and protein selection. '
                        'Supplementary Table 7 reports ordered gene pairs. It cannot validate these reads, samples or exact junctions. '
                        'Table 3 coordinates are retained verbatim; its coordinate convention has not been established here, '
                        'so numeric agreement is not promoted to experimental junction validation. '
                        'Other full protein sequences and author structure coordinates were unavailable.</p>')
        sections.append(table(['Scope','Exact pilot junctions','Junctions with a catalogue-listed pair','Junctions with a NanoString-supported pair'],
            [(name,len(rows),sum(r['published_catalogue_pair_present'] for r in rows),
              sum(r['nanostring_pair_status']=='reported_supported' for r in rows))
             for name,rows in [('Supported RNA',supported_rows),('Selected proteins',selected_rows)]]))
        sections.append(table(['Selected ordered pair','Published catalogue pair','NanoString pair status','Numeric coordinate agreement rows'],
            [(r['ordered_pair'],r['published_catalogue_pair_present'],r['nanostring_pair_status'],r['numeric_coordinate_agreement_rows']) for r in selected_rows]))
        sections.append('<p>'+link(run/'published-comparison/published_comparison.json','Complete comparison and original source rows')+' · '+
                        link(run/'published-comparison/comparison_provenance.json','Comparison timing, hashes and limitations')+'</p>')
    if flagship:
        sections.append('<h2>Gsdmd–Tmem106a discrepancy trace</h2>' + table(['Stage','Pilot result'],[
            ('Assessed exact junctions',len(flagship['assessment_junctions'])),
            ('Assessed supporting/proposed read IDs',len(flagship['assessed_read_ids'])),
            ('Reconstructed read IDs',len(flagship['reconstructed_read_ids'])),
            ('Protein hypotheses',len(flagship['protein_hypotheses'])),
            ('Selected sequences',len(flagship['selected_protein_ids'])),
        ])+'<p>No de novo recovery is claimed. No rescue alignment or published-outcome ranking was used. '
                        'This single sample and bounded supplementary-alignment search do not reproduce the full study; '
                        'biological presence remains UNKNOWN. The separate published control does not fill this gap. '+
                        link(run/'published-comparison/flagship_stage_trace.json','Full stage trace')+'</p>')
    if structures:
        sections.append('<h2>Boltz-2 predictions and confidence</h2><p>One monomer sample per sequence; Boltz 2.2.1, '
                        '3 recycling steps, 200 diffusion steps, step scale 1.5, seed 20260919. Cached public ColabFold MSAs '
                        'were verified against input sequences. The shortest, median and longest available sequences were '
                        'timed before production scheduling. “Verified” means file integrity, exact input sequence and '
                        'finite confidence arrays; it does not validate structural accuracy. Confidence estimates describe the predicted coordinates; '
                        'they do not establish RNA authenticity, protein expression, stable folding or function. '
                        'Low confidence is not by itself a measured disorder annotation. Dashed lines mark the '
                        'projected junction interval (residue offsets) or the control’s 73-residue parental segment.</p>')
        rows=[]
        for job in structures['jobs']:
            label=' / '.join(r.get('gene_name_5p','Gsdmd')+' → '+r.get('gene_name_3p','Tmem106a') for r in job['roles'])
            if any(r['role']=='published_architecture_reference_control' for r in job['roles']):label+=' [separate control]'
            v=job.get('validation',{})
            rows.append((label,job['status'],job['amino_acids'],round(v.get('mean_plddt_0_to_100',0),1) if v else 'Unavailable',
                         round(v.get('fraction_plddt_below50',0)*100,1) if v else 'Unavailable',round(job.get('wall_seconds',0),1)))
        sections.append(table(['Sequence','Status','Residues','Mean pLDDT','% residues pLDDT <50','Wall seconds'],rows))
        verified=[j for j in structures['jobs'] if j['status']=='verified']
        candidate_values=[j['validation']['mean_plddt_0_to_100'] for j in verified
                          if any(r['role']=='pilot_recovered_reference_assisted' for r in j['roles'])]
        controls=[j for j in verified if any(r['role']=='published_architecture_reference_control' for r in j['roles'])]
        if candidate_values:
            sections.append(f'<p>Selected-hypothesis mean pLDDT ranges from {min(candidate_values):.1f} to {max(candidate_values):.1f}. '
                            'A completed prediction is not a confidence pass. The per-residue profiles and PAE matrices '
                            'show uncertainty within and between segments; structural confidence did not change the frozen RNA ranking.</p>')
        if controls:
            v=controls[0]['validation']
            sections.append(f'<p>The separate published architecture control has mean pLDDT {v["mean_plddt_0_to_100"]:.1f}, '
                            f'with {v["fraction_plddt_below50"]*100:.1f}% of residues below 50. '
                            'This run does not establish a confident control conformation or reproduce author coordinates.</p>')
        sections.append('<p>'+link(run/'structures/summary.json','Local sequence/confidence checks, hashes and job outcomes')+' · '+
                        link(run/'fold-inputs/manifest.json','Frozen folding inputs and settings')+' · '+
                        link(run/'fold-inputs/msa-preparation.json','MSA timing and cache records')+'</p>')
        for job in structures['jobs']:
            if job['status']!='verified':continue
            target=run/job['prediction_directory']
            cif=next(relative for relative in job['validation']['files'] if relative.endswith('.cif'))
            pae=next(relative for relative in job['validation']['files'] if Path(relative).name.startswith('pae_') and relative.endswith('.npz'))
            sections.append('<p>'+link(target/cif,'Structure coordinates (mmCIF)')+' · '+link(run/job['confidence_csv'],'Per-residue confidence (CSV)')+' · '+
                            link(target/pae,'PAE array (NPZ)')+' · '+link(target/'validation.json','Confidence metadata and raw file hashes')+'</p>')
            href=html.escape(os.path.relpath(run/job['figure'],output.parent),quote=True)
            sections.append(f'<img src="{href}" alt="Predicted structure, per-residue confidence and predicted aligned error" style="width:100%">')
    if resources:
        sections.append('<h2>Compute and shutdown</h2><p>'+html.escape(resources['interpretation'])+'</p><p>'+link(run/'resource-accounting.json','Resource durations, quoted rates and shutdown evidence')+'</p>')
        sections.append(table(['Resource accounting item','Value'],[
            ('Snapshot UTC',resources['updated_utc']),
            ('Maximum quoted combined USD/hour',round(resources['maximum_quoted_combined_usd_per_hour_upper_bound'],4)),
            ('Accounted compute/storage estimate (USD)',round(resources['estimated_usd_upper_bound_for_accounted_compute_and_storage'],3)),
            ('Temporary workers confirmed stopped',resources['temporary_workers_stopped']),
            ('Shared controller available',resources['controller_left_available'])]))
        diagnostics=[run/'gpu-storage-diagnosis.json',run/'gpu-dependency-diagnosis.json',run/'gpu-compiler-diagnosis.json']
        sections.append('<p>'+' · '.join(link(p,p.stem.replace('-',' ')) for p in diagnostics if p.exists())+'</p>')
    if completion:
        sections.append('<p>'+link(run/'completion-audit.json','Final requirement-by-requirement completion audit')+'</p>')
    sections.append('<h2>Methods and reproducibility</h2><p>'+link(Path('docs/focused_pilot_rules.md'),'Prespecified scientific rules')+' · '+
                    link(run/'selection/selection_rules.md','Frozen selection rules')+' · '+link(Path('docs/focused_pilot_runbook.md'),'Reproduction commands')+' · '+
                    link(run/'rules-prespecified.json','Pre-result method hashes')+' · '+link(run/'discovery-validation.json','Preserved discovery validation')+'</p>')
    sections.append('<h2>Limitations and deferred work</h2><p>Full-cohort processing, SG-NEx, JAFFAL/Genion integration, '
                    'all-protein folding and model training are deferred. The mapping search is finite and proposals '
                    'come from supplementary alignments; unmapped or soft-clipped reads are not exhaustively rescued. '
                    'Reference assistance assumes alleles at low-quality discrepancies. NMD remains unknown without '
                    'full transcript architecture. Structural confidence cannot establish expression or function. '
                    'Published pair-level evidence cannot confirm an individual junction, read or sample. '
                    'Independent human review has not been recorded.</p><p>'+
                    link(run/'postfreeze-review-notes.md','Automated post-freeze review notes; no reranking')+' · '+
                    link(run/'deferred-work.json','Explicit deferred-work ledger')+'</p>')
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' + \
           '<title>Chimeric RNA focused pilot</title><style>body{max-width:1150px;margin:2rem auto;padding:0 1rem;font:16px/1.5 system-ui;color:#203040}' + \
           'table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #ccd5dd;padding:8px;text-align:left;overflow-wrap:anywhere}' + \
           'th{background:#edf3f6}svg{width:100%;max-width:900px}a{color:#126878}</style><body>' + ''.join(sections) + '</body></html>'
    output.write_text(page)
    return {'status': 'complete_report' if complete else 'progress_report', 'path': str(output), 'rna_junctions': len(ranking),
            'selected_proteins': len(selection['selected'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=Path('runs/focused-pilot-20260919'))
    parser.add_argument('--output', type=Path, default=Path('reports/focused_pilot.html'))
    args = parser.parse_args()
    print(json.dumps(render(args.run, args.output), indent=2))


if __name__ == '__main__':
    main()
