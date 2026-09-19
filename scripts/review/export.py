"""Export the verified, frozen review records for an offline browser view."""
import hashlib
import json
from pathlib import Path
from verify import validate_decision
ROOT=Path(__file__).resolve().parents[2]

def build(root=ROOT):
    freeze=json.loads((root/'results/review/case_freeze.json').read_text())
    cases=[]
    for item in freeze['cases']:
        pair=item['pair_id']
        slug=pair.lower().replace(':','-')
        run=root/'results/review'/slug
        decision_path=run/'decision.json'
        decision=json.loads(decision_path.read_text())
        steps=[json.loads(p.read_text()) for p in sorted(run.glob('step-*.json'))]
        validate_decision(decision,steps)
        cases.append({'slug':slug,'selection_reason':item['reason'],'decision':decision,'steps':steps,
                      'decision_sha256':hashlib.sha256(decision_path.read_bytes()).hexdigest()})
    return {'schema_version':1,'mode':'recorded_codex_review','cases':cases,'case_freeze':freeze,
            'notice':'Recorded Codex decisions and actual tool outputs. No live model or GPU call occurs in this page. Scientist review is a local, self-reported record, not independent authentication.'}

if __name__=='__main__':
    out=ROOT/'demo/review';out.mkdir(exist_ok=True)
    value=json.dumps(build(),ensure_ascii=False,allow_nan=False,separators=(',',':'))
    (out/'data.json').write_text(value+'\n')
    (out/'data.js').write_text('window.REVIEW_DATA='+value.replace('<','\\u003c')+';\n')
    print('Exported three source-linked recorded review cases.')
