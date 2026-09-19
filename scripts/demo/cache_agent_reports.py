"""Package the five already-authored Codex reports with exact evidence/prompt provenance.
This does not invoke a model or create new model-authored prose; drafts are retained verbatim.
"""
import json
from datetime import datetime,timezone
from reports import ROOT,PROMPT,report_input,digest,validate_report
x=json.loads((ROOT/'demo/data.json').read_text());sources=json.loads((ROOT/'results/demo/sources/passages.json').read_text());drafts=json.loads((ROOT/'results/demo/agent_report_drafts.json').read_text())
for c in x['candidates']:
 if c['pair_id'] not in drafts:continue
 inputs=report_input(c,sources)
 report={'pair_id':c['pair_id'],'claims':drafts[c['pair_id']],'numeric_claims':[{'field':'long_read_support','value':c['long_read_support']}],'generator':'Codex agent-authored · cached (no API call)','provenance':{'model':'gpt-6-astra','reasoning_effort':'high','execution':'Codex agent authored from actual candidate rows and retrieved user-supplied primary PDF passages; packaged locally, not Responses API','authored_at':'2026-09-19','packaged_at':datetime.now(timezone.utc).isoformat(),'prompt':PROMPT,'authoring_instruction_excerpt':'after real results, you as agent can synthesize 5 candidate reports from actual input rows and paper passages, record generator="Codex agent (gpt-6-astra, high)", cached/offline, source snapshots and exact prompts in provenance. Distinguish these from deterministic evidence summaries, never pretend API calls occurred.','input':inputs,'input_sha256':digest(inputs),'validation':'Citation identifiers, numeric prose tokens and structured numeric values validated; qualitative claims manually reviewed against supplied passages.'}}
 validate_report(report,inputs)
 (ROOT/'results/demo/reports'/f"{c['pair_id'].replace(':','__')}.json").write_text(json.dumps(report,indent=2))
 print('Validated',c['pair_id'])
