import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


spec=importlib.util.spec_from_file_location('boltz_worker_controller',Path(__file__).resolve().parents[1]/'scripts/run_boltz_worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


def test_gpu_partial_create_failure_stops_owned_resource(monkeypatch,tmp_path):
    run=tmp_path/'worker'
    monkeypatch.setattr(worker,'RUN',run)
    monkeypatch.setattr(worker.transport,'RUN',run)
    monkeypatch.setattr(worker,'validate_inputs',lambda _: {})
    monkeypatch.setattr(worker,'preflight',lambda: {'allowed':True})
    monkeypatch.setattr(worker.time,'time',lambda:1789830600)
    monkeypatch.setattr(worker.subprocess,'Popen',lambda *a,**kw:SimpleNamespace(pid=123))
    calls=[]
    def command(label,*args,**kwargs):
        calls.append(label)
        raise RuntimeError('partial GPU provisioning failure')
    monkeypatch.setattr(worker,'command',command)
    monkeypatch.setattr(worker.transport,'stop_owned',lambda:calls.append('stop_owned') or 'STOPPED')
    with pytest.raises(RuntimeError,match='partial GPU provisioning'):
        worker.main(tmp_path)
    assert calls==['create','stop_owned']
    assert (run/'shutdown-confirmed.json').is_file()
    with pytest.raises(RuntimeError,match='Existing folding attempt'):
        worker.main(tmp_path)


def test_gpu_unknown_resource_fails_before_quote_or_launch(monkeypatch):
    monkeypatch.setattr(worker.transport,'inventory',lambda:[{'name':'chrna-controller'}, {'name':'unpriced-worker'}])
    with pytest.raises(RuntimeError,match='Unpriced'):
        worker.preflight()


@pytest.mark.parametrize('status',['RUNNING','STOPPING'])
def test_gpu_resume_rejects_nonterminal_previous_lease(monkeypatch,tmp_path,status):
    monkeypatch.setattr(worker,'RESUME_FROM',tmp_path)
    (tmp_path/'shutdown-confirmed.json').write_text(json.dumps({'status':status}))
    (tmp_path/'actual-launch.json').write_text(json.dumps({'instances':[{'name':worker.NAME,'instance_type':worker.TYPE,'id':'owned'}]}))
    monkeypatch.setattr(worker.transport,'inventory',lambda:[])
    with pytest.raises(RuntimeError,match='not safely resumable'):
        worker.preflight()


def test_gpu_resume_rejects_changed_worker_identity(monkeypatch,tmp_path):
    monkeypatch.setattr(worker,'RESUME_FROM',tmp_path)
    (tmp_path/'shutdown-confirmed.json').write_text(json.dumps({'status':'STOPPED'}))
    (tmp_path/'actual-launch.json').write_text(json.dumps({'instances':[{'name':worker.NAME,'instance_type':worker.TYPE,'id':'owned'}]}))
    monkeypatch.setattr(worker.transport,'inventory',lambda:[
        {'name':'chrna-controller','id':'2gnfmgobs','instance_type':'cpu-e2.4vcpu-16gb'},
        {'name':worker.NAME,'id':'someone-else','instance_type':worker.TYPE,'status':'STOPPED'}])
    with pytest.raises(RuntimeError,match='identity changed'):
        worker.preflight()
