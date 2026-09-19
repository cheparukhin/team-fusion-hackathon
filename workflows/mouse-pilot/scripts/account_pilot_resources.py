"""Account for observed lease intervals using preserved conservative public quotes."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from run_pilot_worker import inventory
from boltz_worker import save


def rates(row):
    quote=row['quote']
    compute=max(float(p['amount']) for p in [quote['basePrice'],*quote.get('locationPrices',{}).values()])
    units=math.ceil(row['disk_gib_upper_bound']*1024**3/10**9)
    storage=units*max(float(s['pricePerGbHr']['amount']) for s in quote['supportedStorage'])
    return compute,storage


def main(run):
    now=datetime.now(timezone.utc)
    episodes=[];resource_rates={};first_seen={};peak=[]
    for directory in [run,run/'retry-1',run/'connectivity-debug',run/'retry-2',*sorted(p for p in run.glob('folding-worker*') if p.is_dir())]:
        budget_path=directory/'launch-budget.json'
        if not budget_path.exists():continue
        budget=json.loads(budget_path.read_text())
        if budget['currency']!='USD':raise ValueError('Unknown currency')
        resources=budget['resources']
        if isinstance(resources,dict):
            resources=[{**r,'name':'chrna-controller' if sku.startswith('cpu-e2') else 'chrna-pilot-cpu-20260919'} for sku,r in resources.items()]
        for row in resources:
            name=row['name'];compute,storage=rates(row)
            old=resource_rates.get(name,(0,0));resource_rates[name]=(max(old[0],compute),max(old[1],storage))
        peak.append(sum(sum(rates(r)) for r in resources))
        lease_path=directory/'lease.json'
        if not lease_path.exists():continue
        lease=json.loads(lease_path.read_text());name=lease['name']
        start=datetime.fromisoformat(lease.get('created_utc',budget['utc']))
        first_seen[name]=min(first_seen.get(name,start),start)
        first_seen['chrna-controller']=min(first_seen.get('chrna-controller',start),start)
        shutdown_path=directory/'shutdown-confirmed.json'
        shutdown=json.loads(shutdown_path.read_text()) if shutdown_path.exists() else None
        stop=datetime.fromisoformat(shutdown['utc']) if shutdown else now
        if stop<start:raise ValueError('Shutdown precedes lease')
        worker_row=next(r for r in resources if r['name']==name)
        compute,_=rates(worker_row)
        seconds=(stop-start).total_seconds()
        episodes.append({'name':name,'attempt':str(directory.relative_to(run)),'start_utc':start.isoformat(),
                         'stop_or_snapshot_utc':stop.isoformat(),'lease_wall_seconds':seconds,
                         'status':shutdown['status'] if shutdown else 'not_confirmed_stopped',
                         'quoted_compute_usd_per_hour_upper_bound':compute,'compute_usd_estimate_upper_bound':compute*seconds/3600,
                         'quote_record':str(budget_path.relative_to(run)),
                         'shutdown_record':str(shutdown_path.relative_to(run)) if shutdown else None})
    persistent=[]
    for name,start in first_seen.items():
        compute,storage=resource_rates[name];hours=(now-start).total_seconds()/3600
        persistent.append({'name':name,'accounting_start_utc':start.isoformat(),'accounting_hours':hours,
                           'storage_usd_per_hour_upper_bound':storage,'storage_usd_estimate_upper_bound':storage*hours,
                           'controller_compute_usd_estimate_upper_bound':compute*hours if name=='chrna-controller' else 0})
    current=inventory()
    unknown={w['name'] for w in current}-set(resource_rates)
    if unknown:raise ValueError('Unaccounted current resources: '+str(sorted(unknown)))
    result={'status':'quote_based_usage_estimate','updated_utc':now.isoformat(),'currency':'USD',
            'interpretation':'Observed lease intervals and maximum quoted regional compute/storage rates; conservative estimate, not a provider invoice. Provisioning through confirmed shutdown is charged in full. Persistent storage is included through this snapshot and may continue after workers stop. Costs before the first focused launch, taxes and unquoted network charges are not established here.',
            'episodes':episodes,'persistent_resources':persistent,'live_inventory':current,
            'maximum_quoted_combined_usd_per_hour_upper_bound':max(peak),
            'estimated_usd_upper_bound_for_accounted_compute_and_storage':sum(e['compute_usd_estimate_upper_bound'] for e in episodes)+sum(p['storage_usd_estimate_upper_bound']+p['controller_compute_usd_estimate_upper_bound'] for p in persistent),
            'temporary_workers_stopped':all(e['status'] in ('STOPPED','DELETED','absent') for e in episodes) and all(w['status'] in ('STOPPED','DELETED') for w in current if w['name']!='chrna-controller'),
            'controller_left_available':any(w['name']=='chrna-controller' and w['status']=='RUNNING' for w in current)}
    save(run/'resource-accounting.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('episodes','persistent_resources','live_inventory')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=Path('runs/focused-pilot-20260919'))
    main(parser.parse_args().run.resolve())
