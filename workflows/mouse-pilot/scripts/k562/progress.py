"""Persist an honest progress/report view while the detached controller runs."""
import datetime,html,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'runs/k562-pilot/20260919-overnight';NAME='chrna-k562-cpu-20260919'
def read(p,default=None):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return {} if default is None else default

def render():
 remote=read(RUN/'progress-snapshot.json');controller=read(RUN/'controller.json');account=read(RUN/'resource-accounting.json');shutdown=read(RUN/'shutdown.json');budget=read(RUN/'budget.json');lease=read(RUN/'lease.json')
 local=RUN/'outputs'
 def datum(name):return read(local/name) or remote.get(name,{})
 status=datum('status.json');completion=datum('completion.json');repeat=datum('repeatability.json');corr=datum('corroboration.json')
 names=['SGNex_K562_directRNA_replicate4_run1','SGNex_K562_directRNA_replicate5_run1'];summaries=[datum(n+'/assessment/assessment_summary.json') for n in names]
 stages=[('Inputs and settings frozen',(RUN/'source-freeze.json').exists()),('CPU worker ready',(RUN/'actual-hardware.log').exists() and controller.get('status')!='provisioning'),('Direct RNA library A',bool(summaries[0])),('Direct RNA library B',bool(summaries[1])),('Real-read repeatability',repeat.get('equal') is True),('Illumina corroboration',corr.get('illumina',{}).get('status')=='processed'),('Results copied and verified',bool(read(RUN/'preservation.json'))),('Temporary compute stopped',shutdown.get('status') in ['STOPPED','DELETED','ABSENT'])]
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();count=sum(x[1] for x in stages)
 hours=max(0,(time.time()-(lease.get('expires_epoch',time.time()+28800)-28800))/3600)
 rate=budget.get('resources',[{}])[-1].get('usd_per_hour_bound',0)
 cost=account.get('quoted_compute_upper_bound_usd',hours*rate)
 if shutdown:
  phase='Completed' if completion.get('A_execution')=='complete' and completion.get('B_execution')=='processed' and repeat.get('equal') and read(RUN/'preservation.json') else 'Stopped — review stage outcomes'
 else:phase=status.get('stage',controller.get('status','Preparing'))
 cards=''.join('<li class="'+('done' if done else 'pending')+'">'+('✓ ' if done else '○ ')+html.escape(label)+'</li>' for label,done in stages)
 bars=''
 for label,summary in zip(['Library A','Library B'],summaries):
  total=summary.get('exact_junctions');supported=summary.get('supported_exact_junctions');reads=summary.get('assessed_split_reads')
  if total is not None:
   bars+='<div class="barlabel">'+label+f': {supported:,} / {total:,} proposals meet mapping criteria; {reads:,} split reads assessed</div><div class="bar"><span style="width:'+str(100*supported/max(total,1))+'%"></span></div>'
  else:bars+='<p>'+label+': pending</p>'
 errors={k:v for k,v in {'controller':controller.get('error'),'workflow':datum('failure.json'),'illumina':datum('illumina/failure.json'),'preservation':controller.get('preservation_error')}.items() if v}
 payload={'updated_utc':stamp,'phase':phase,'stages_complete':count,'stages_total':len(stages),'quoted_cost_bound_usd':cost,'summaries':summaries,'corroboration':corr,'repeatability':repeat,'shutdown':shutdown,'errors':errors}
 (RUN/'progress.json').write_text(json.dumps(payload,indent=2)+'\n')
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>K562 overnight verification</title><style>body{font:16px system-ui,sans-serif;background:#f4f6fa;color:#18253b;max-width:1060px;margin:35px auto;padding:0 22px}h1{font-size:32px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}.card{background:white;border:1px solid #d8e0e8;border-radius:12px;padding:20px;margin:16px 0}.big{font-size:30px;font-weight:700}ul{list-style:none;padding:0}li{padding:10px 0;border-bottom:1px solid #e7eaf0}.done{color:#08735e}.pending{color:#536379}.bar{height:16px;background:#dfe5ef;border-radius:5px;margin:7px 0 20px;overflow:hidden}.bar span{display:block;height:100%;background:#237cbe}.barlabel{margin-top:18px}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#165f9d}small{color:#536379}</style><h1>K562 overnight verification</h1>'''
 page+='<p>'+html.escape(phase)+'</p><small>Snapshot '+stamp+' · refresh to read the latest saved state</small><div class="grid"><div class="card"><div class="big">'+str(count)+' / '+str(len(stages))+'</div>stages complete (not a time estimate)</div><div class="card"><div class="big">$'+f'{cost:.2f}'+'</div>quoted cost upper estimate; billing not yet reconciled</div><div class="card"><div class="big">$20</div>run allowance · eight-hour worker lease</div></div>'
 page+='<div class="card"><h2>Execution</h2><ul>'+cards+'</ul></div><div class="card"><h2>RNA mapping evidence</h2>'+bars+'<p>Mapping support is not biological validation. Uncorroborated junctions remain unknown; specimen independence, internal adapters, and RNA origin are not established.</p></div>'
 if corr:page+='<div class="card"><h2>Independent evidence joins</h2><pre>'+html.escape(json.dumps(corr,indent=2))+'</pre></div>'
 if errors:page+='<div class="card"><h2>Issues requiring review</h2><pre>'+html.escape(json.dumps(errors,indent=2))+'</pre></div>'
 if (local/'report.html').exists():page+='<p><a href="outputs/report.html">Detailed scientific report</a> · <a href="outputs/primary_candidates.tsv">Candidate table</a></p>'
 page+='<p>No GPU, Hi-C, or protein prediction in this run. Other users’ instances are not modified. Cost estimates cover this temporary worker; other account activity is separate.</p></html>'
 tmp=RUN/'progress.html.partial';tmp.write_text(page);tmp.replace(RUN/'progress.html')

def main():
 paths=['status.json','completion.json','failure.json','repeatability.json','corroboration.json','illumina/failure.json']+[n+'/assessment/assessment_summary.json' for n in ['SGNex_K562_directRNA_replicate4_run1','SGNex_K562_directRNA_replicate5_run1']]
 code="import pathlib,json; b=pathlib.Path('/home/ubuntu/k562-external/outputs'); paths="+repr(paths)+"; print(json.dumps({p:json.loads((b/p).read_text()) for p in paths if (b/p).exists()}))"
 import shlex
 while True:
  if (RUN/'actual-launch.json').exists() and not (RUN/'shutdown.json').exists():
   try:
    r=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10',NAME,'python3 -c '+shlex.quote(code)],text=True,capture_output=True,timeout=20)
    if r.returncode==0:
     data=json.loads(r.stdout);(RUN/'progress-snapshot.json').write_text(json.dumps(data,indent=2)+'\n')
   except (OSError,ValueError,subprocess.TimeoutExpired):pass
  render()
  if (RUN/'resource-accounting.json').exists():return
  pid=read(RUN/'dispatch.json').get('pid')
  if pid:
   try:os.kill(pid,0)
   except ProcessLookupError:return
  time.sleep(45)
if __name__=='__main__':main()
