import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('budget', Path(__file__).resolve().parents[1] / 'scripts/check_budget.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_hourly_limit_is_aggregate_and_fails_closed():
    policy = {'max_combined_hourly_rate': 100}
    assert module.check(policy, [0.13], 2.5)['combined_usd_per_hour'] == pytest.approx(2.63)
    with pytest.raises(ValueError):
        module.check(policy, [50], 51)
    for invalid in [None, float('nan'), float('inf'), -1, True]:
        with pytest.raises(ValueError):
            module.check(policy, [], invalid)


def test_owner_revised_policy_includes_controller_and_hard_ceiling():
    import json
    policy = json.loads((Path(__file__).resolve().parents[1] / 'infra/budget-policy.json').read_text())
    assert policy['currency'] == 'USD'
    assert policy['preferred_combined_hourly_rate'] == 100
    assert module.check(policy, [0.2, 99], 400)['combined_usd_per_hour'] == pytest.approx(499.2)
    with pytest.raises(ValueError):
        module.check(policy, [0.2, 100], 400)
