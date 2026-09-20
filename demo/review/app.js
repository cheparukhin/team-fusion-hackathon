'use strict';
const $=id=>document.getElementById(id), esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const data=window.REVIEW_DATA, drafts=new Map();
const toolNames={retrieve_candidate:'Retrieve evidence',compare_probe_junctions:'Compare junctions',rematch_parabricks:'Check NVIDIA output',inspect_structure:'Inspect structure',retrieve_sources:'Read primary source'};
const subtitles={'psap-lgals3':'High score · junction conflict','gsdmd-tmem106a':'Published evidence · uncertain fold','cd274-lacc1':'RNA support · missing structure'};
let current=data.cases.find(c=>c.slug===location.hash.slice(1))||data.cases[0], stepIndex=0, saved=null;
const fmt=(n,d=0)=>Number(n).toLocaleString('en-GB',{maximumFractionDigits:d,minimumFractionDigits:d});
const tool=(name)=>current.steps.find(s=>s.tool===name)?.output;
const key=()=>`chrna-review-v1:${current.decision_sha256}`;
function path(file){return `../../results/review/${current.slug}/${file}`;}
function facts(items){return `<div class="fact-grid">${items.map(([n,l])=>`<div><strong>${esc(n)}</strong><span>${esc(l)}</span></div>`).join('')}</div>`;}
function renderEvidence(){
 const c=tool('retrieve_candidate'),comparison=tool('compare_probe_junctions'),gpu=tool('rematch_parabricks'),structure=tool('inspect_structure');
 let html='';
 if(current.slug==='psap-lgals3'){
  const p=comparison.comparisons[0],nearest=p.published_offsets[0];
  html=`<div class="eyebrow">A JUNCTION TO RESOLVE</div><div class="evidence-number">${fmt(p.closest_max_offset_nt)}<span>nt</span></div><p class="evidence-caption">between the nearest recorded read endpoint and the designed probe on the second parent.</p><div class="junction-line"><div>Nearest read · chr14<strong>${fmt(nearest.published_breakpoint2)}</strong></div><div>Designed probe · chr14<strong>${fmt(p.probe_breakpoint2)}</strong></div></div>${facts([[c.long_read_support,'Published read IDs · pair-level'],[fmt(c.score_rna,3),'RNA score · not a probability'],['Unknown','Per-probe testing / QC']])}<div class="caution">The score ranks the pair. It does not resolve which junction the probe tests. Check the original read alignment and coordinate convention before interpreting the discrepancy. <a href="../../results/review/psap_source_audit.json">Direct source audit ↗</a></div>`;
 }else if(structure?.status==='available'){
  const confidence=structure.predictions[0].confidence.mean_plddt;
  html=`<div class="eyebrow">PUBLISHED EVIDENCE / PREDICTED STRUCTURE</div><div class="evidence-number">${fmt(confidence,1)}<span>pLDDT</span></div><p class="evidence-caption">Mean confidence of the cached Boltz2 chimera model. Its fold remains uncertain.</p><div class="confidence-track" aria-label="Mean model confidence ${fmt(confidence,1)} out of 100"><span class="confidence-marker" style="left:${Math.max(0,Math.min(100,confidence))}%"></span></div><div class="confidence-labels"><span>0 · lower confidence</span><span>100 · higher confidence</span></div>${facts([['Reported','Published NanoString support'],[gpu.support,'Matching reads · bounded pilot'],[fmt(comparison.comparisons[0].closest_max_offset_nt)+' nt','Read / probe endpoint offset']])}<div class="caution">The paper reports protein and functional experiments as well as RNA evidence. Our uncertain fold and pilot non-detection do not contradict those findings. <a href="https://www.nature.com/articles/s41586-026-10982-x">Primary paper · Figures 3–4 ↗</a></div>`;
 }else{
  html=`<div class="eyebrow">AN UNANSWERED PROTEIN QUESTION</div><div class="evidence-number" style="font-size:38px">Structure unavailable</div><p class="evidence-caption">The project has no candidate-specific model for this pair. Published RNA evidence still stands on its own.</p>${facts([['Reported','Published NanoString support'],[c.long_read_support,'Published long-read ID'],[gpu.support,'Matching reads · bounded pilot']])}<div class="caution">A missing model is not a negative experiment. The primary paper reports this RNA junction; translation and function remain separate questions in these project artifacts.</div>`;
 }
 $('evidence').innerHTML=html;
}
function stepSummary(s){
 const o=s.output;
 if(s.tool==='retrieve_candidate')return `${fmt(o.long_read_support)} published read ID${o.long_read_support===1?'':'s'} at the pair level. NanoString reporting: ${o.label===1?'reported supported':'not reported supported'}. Per-probe QC: ${o.assay_qc_status}.`;
 if(s.tool==='compare_probe_junctions')return o.comparisons.map(c=>c.closest_max_offset_nt===null?'No comparable ordered breakpoint records.':`Closest endpoint discrepancy: ${fmt(c.closest_max_offset_nt)} nt. This is a coordinate comparison, not an authenticity verdict.`).join(' ');
 if(s.tool==='rematch_parabricks')return o.support===null?'Independent alignment evidence is unavailable.':`${fmt(o.support)} matching probe-junction read IDs in ${fmt(o.read_pairs)} read pairs, using the original ±${o.tolerance_nt}-nt rule. Non-detection does not establish absence.`;
 if(s.tool==='inspect_structure')return o.status==='available'?`Cached ${o.predictions[0].method}. Mean pLDDT ${fmt(o.predictions[0].confidence.mean_plddt,1)}. No experimental structure or functional validation is implied.`:'No candidate-specific structure is available in the project manifest.';
 return `Retrieved ${o.passages.length} fixed primary-paper passages. The assistant checked whether the passage explicitly supports the pair-specific claim.`;
}
function renderStep(){
 const s=current.steps[stepIndex];
 $('step-count').textContent=`${stepIndex+1} / ${current.steps.length}`;
 $('previous').disabled=stepIndex===0;$('next').disabled=stepIndex===current.steps.length-1;
 $('step-nav').innerHTML=current.steps.map((s,i)=>`<button type="button" data-step="${i}" ${i===stepIndex?'aria-current="step"':''}>${i+1} · ${esc(toolNames[s.tool])}</button>`).join('');
 $('step-detail').innerHTML=`<div class="eyebrow">CHECK ${s.step} / ${esc(toolNames[s.tool])}</div><h3>${esc(s.action_reason)}</h3><div class="step-output">${esc(stepSummary(s))}</div><p class="step-meta">Executed ${esc(new Date(s.executed_at).toISOString().replace('T',' ').slice(0,19))} UTC · ${fmt(s.duration_seconds,3)} s tool time · not total review time</p><details><summary>Inspect full recorded output and source hashes</summary><pre>${esc(JSON.stringify(s.output,null,2))}</pre>${s.sources.map(source=>`<p><a href="../../${esc(source.path)}">${esc(source.path)}</a><br><code>${esc(source.sha256)}</code></p>`).join('')}<a href="${path(`step-${String(s.step).padStart(2,'0')}.json`)}">Open this complete tool record ↗</a></details>`;
}
function validReceipt(r){return r&&r.decision_sha256===current.decision_sha256&&r.pair_id===current.decision.pair_id&&typeof r.reviewer==='string'&&r.reviewer.trim()&&typeof r.note==='string'&&r.note.trim()&&['endorse_next_step','revise_next_step','defer'].includes(r.verdict)&&Number.isFinite(Date.parse(r.reviewed_at));}
function renderSaved(){
 saved=null;let unavailable=false;
 try{const raw=localStorage.getItem(key());if(raw){const parsed=JSON.parse(raw);if(validReceipt(parsed))saved=parsed;}}
 catch(e){unavailable=true;}
 $('saved-status').textContent=saved?`Local review saved by ${saved.reviewer} · ${new Date(saved.reviewed_at).toLocaleString()}`:unavailable?'Browser storage is unavailable. Saving will offer a downloadable record instead.':'No scientist review recorded in this browser.';
 $('download').hidden=!saved;$('clear').hidden=!saved;
 const draft=drafts.get(current.slug)||saved||{};
 $('reviewer').setCustomValidity('');$('note').setCustomValidity('');
 $('reviewer').value=draft.reviewer||'';$('verdict').value=draft.verdict||'';$('note').value=draft.note||'';
}
function render(){
 const d=current.decision;
 $('cases').innerHTML=data.cases.map(c=>`<button type="button" data-case="${c.slug}" aria-pressed="${c===current}"><strong>${esc(c.decision.pair_id.replace(':','–'))}</strong><small>${esc(subtitles[c.slug])}</small></button>`).join('');
 $('case-heading').innerHTML=`<h2>${esc(d.pair_id.replace(':','–'))}</h2><p>Mouse macrophages · GRCm39 · selected demonstration case</p>`;
 renderEvidence();$('decision-title').textContent=d.headline;$('recommendation').textContent=d.recommendation;
 const a=d.next_action;
 $('next-action').innerHTML=`<div class="next-action"><h3>The question</h3><p>${esc(a.question)}</p><h3>First, resolve this</h3><p>${esc(a.first_step)}</p><details><summary>Proposed experiment and its limits</summary><p>${esc(a.proposed_experiment)}</p><p>${esc(a.discriminating_outcome)}</p><p class="small">Proposal only. Not executed.</p></details></div>`;
 $('decision-source').href=path('decision.json');
 $('claim-list').innerHTML=d.claims.map(c=>`<article class="claim"><span class="kind">${esc(c.kind)}</span><div><p>${esc(c.text)}</p>${[...new Set(c.evidence.map(e=>e.step))].map(n=>`<a href="#step-detail" data-evidence="${n-1}">Check ${n} · ${esc(toolNames[current.steps[n-1].tool])} ↗</a>`).join('')}</div></article>`).join('');
 renderStep();renderSaved();
}
function switchCase(slug){
 if(slug===current.slug)return;
 drafts.set(current.slug,{reviewer:$('reviewer').value,verdict:$('verdict').value,note:$('note').value});
 current=data.cases.find(c=>c.slug===slug)||current;stepIndex=0;try{history.replaceState(null,'',`#${current.slug}`);}catch(e){}render();$('cases').querySelector(`[data-case="${current.slug}"]`)?.focus();
}
$('cases').addEventListener('click',e=>{const b=e.target.closest('[data-case]');if(b)switchCase(b.dataset.case);});
$('step-nav').addEventListener('click',e=>{const b=e.target.closest('[data-step]');if(b){stepIndex=Number(b.dataset.step);renderStep();$('step-nav').querySelector(`[data-step="${stepIndex}"]`)?.focus();}});
$('previous').onclick=()=>{if(stepIndex>0){stepIndex--;renderStep();}};
$('next').onclick=()=>{if(stepIndex<current.steps.length-1){stepIndex++;renderStep();}};
$('claim-list').addEventListener('click',e=>{const link=e.target.closest('[data-evidence]');if(link){e.preventDefault();stepIndex=Number(link.dataset.evidence);renderStep();$('step-detail').focus({preventScroll:true});$('step-detail').scrollIntoView({block:'center'});}});
function download(record){const blob=new Blob([JSON.stringify(record,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`chrna-review-${current.slug}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('review-form').addEventListener('submit',e=>{
 e.preventDefault();
 for(const id of ['reviewer','note']){$(id).setCustomValidity($(id).value.trim()?'':'Please enter a non-empty value.');}
 if(!$('review-form').reportValidity())return;
 saved={schema_version:1,pair_id:current.decision.pair_id,decision_sha256:current.decision_sha256,reviewer:$('reviewer').value.trim(),verdict:$('verdict').value,note:$('note').value.trim(),reviewed_at:new Date().toISOString(),record_type:'self_reported_local_scientist_review',scope:'Review of the proposed next step, not certification of biological truth or evidence that an experiment was performed.',authentication:'Reviewer name and device timestamp are self-reported; no identity verification.'};
 drafts.delete(current.slug);
 try{localStorage.setItem(key(),JSON.stringify(saved));$('saved-status').textContent=`Local review saved by ${saved.reviewer}. Download it to share.`;$('download').hidden=false;$('clear').hidden=false;}
 catch(err){$('saved-status').textContent='Browser storage is unavailable. Your review record is being downloaded.';download(saved);$('download').hidden=false;}
});
for(const id of ['reviewer','note'])$(id).addEventListener('input',()=>$(id).setCustomValidity(''));
$('download').onclick=()=>{if(saved)download(saved);};
$('clear').onclick=()=>{try{localStorage.removeItem(key());}catch(e){}drafts.delete(current.slug);saved=null;renderSaved();};
render();
