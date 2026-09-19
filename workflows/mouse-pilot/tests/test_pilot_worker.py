import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('pilot_worker', Path(__file__).resolve().parents[1]/'scripts/run_pilot_worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def test_create_failure_preserves_then_stops_without_retry(monkeypatch, tmp_path):
    monkeypatch.setattr(worker, 'RUN', tmp_path)
    monkeypatch.setattr(worker, 'BASE', tmp_path)
    (tmp_path/'tools-and-script.tar.gz').write_bytes(b'test')
    monkeypatch.setattr(worker, 'preflight', lambda: {'allowed':True})
    monkeypatch.setattr(worker.time, 'time', lambda: 1789830600)
    monkeypatch.setattr(worker.subprocess, 'Popen', lambda *a, **kw: SimpleNamespace(pid=123))
    calls=[]
    def command(label, *args, **kwargs):
        calls.append(label)
        if label=='create':
            raise RuntimeError('provider failure after possible partial launch')
        return 0
    monkeypatch.setattr(worker, 'command', command)
    monkeypatch.setattr(worker, 'stop_owned', lambda: calls.append('stop_owned') or 'STOPPED')
    with pytest.raises(RuntimeError, match='provider failure'):
        worker.main()
    assert calls == ['create','stop_owned']
    assert (tmp_path/'shutdown-confirmed.json').exists()
    with pytest.raises(RuntimeError, match='Lease already exists'):
        worker.main()


def test_inventory_change_fails_before_quote_or_launch(monkeypatch):
    monkeypatch.setattr(worker, 'inventory', lambda: [{'name':'unpriced-teammate-instance'}])
    with pytest.raises(RuntimeError, match='Inventory changed'):
        worker.preflight()


def test_stop_owns_only_named_worker(monkeypatch):
    monkeypatch.setattr(worker, 'inventory', lambda: [{'name':'chrna-controller','status':'RUNNING'}])
    monkeypatch.setattr(worker, 'command', lambda *a, **kw: pytest.fail('must not stop controller'))
    assert worker.stop_owned()=='absent'


def test_brev_transport_uses_real_shell_without_changing_account(monkeypatch):
    monkeypatch.setenv('SHELL', '/usr/sbin/nologin')
    assert worker.transport_env()['SHELL'] == '/bin/sh'
    assert worker.os.environ['SHELL'] == '/usr/sbin/nologin'


def test_ssh_probe_retries_before_declaring_ready(monkeypatch, tmp_path):
    monkeypatch.setattr(worker, 'RUN', tmp_path)
    monkeypatch.setattr(worker.time, 'sleep', lambda _: None)
    calls = []
    results = iter([255, 0])
    def command(label, argv, **kwargs):
        calls.append((label, argv))
        return next(results) if label.startswith('ssh-probe') else 0
    monkeypatch.setattr(worker, 'command', command)
    worker.wait_for_ssh()
    assert [x[0] for x in calls] == ['ssh-refresh-1', 'ssh-probe-1', 'ssh-refresh-2', 'ssh-probe-2']
    assert (tmp_path/'ssh-ready.json').exists()
