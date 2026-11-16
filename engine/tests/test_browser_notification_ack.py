"""Notification acknowledgements remain scoped, audited and repeatable."""
import importlib.util
from pathlib import Path

import pytest

from vigile.store import Store

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('browser_monitoring_test', ROOT / 'web-local/src/browser_monitoring.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_ack_is_audited_idempotent_and_cannot_cross_profiles():
    store = Store(':memory:')
    event = {'id': 'event-1', 'subject_id': 'crew-a', 'mission_id': 'browser-mission', 'kind': 'CLINICAL_CRITERIA'}
    store.put('monitoring_event', event['id'], event)
    first = MODULE.LocalBiomedical.__new__(MODULE.LocalBiomedical)
    first.store, first.owner = store, 'crew-a'
    result = first.dispatch('notification_ack', {'id': event['id']})
    checkpoint = store.checkpoint()
    assert first.dispatch('notification_ack', {'id': event['id']}) == result
    assert store.checkpoint() == checkpoint
    assert store.get('monitoring_event', event['id']) == event
    with pytest.raises(ValueError, match='NOTIFICATION_SCOPE_MISMATCH'):
        other = MODULE.LocalBiomedical.__new__(MODULE.LocalBiomedical)
        other.store, other.owner = store, 'crew-b'
        other.dispatch('notification_ack', {'id': event['id']})
    assert store.verify()
    store.close()
