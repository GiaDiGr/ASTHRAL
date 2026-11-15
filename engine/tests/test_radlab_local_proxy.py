from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit
import io
import json
import sys

import pytest

WEB_LOCAL = Path(__file__).resolve().parents[2] / 'web-local'
sys.path.insert(0, str(WEB_LOCAL))
import radlab_proxy


def query(**overrides):
    values = {
        'startDate': '2023-01-01', 'endDate': '2023-01-01', 'spacecraft': 'ISS',
        'quantities': 'absorbed_dose_rate,dose_equivalent_rate,flux',
    }
    values.update(overrides)
    return urlencode(values)


def test_upstream_url_uses_fixed_nasa_host_and_documented_radlab_field_units():
    url = radlab_proxy.build_radlab_upstream_url(query(instrumentId='REM-Lid'))
    parsed = urlsplit(url)
    params = parse_qsl(parsed.query, keep_blank_values=True)
    values = dict(params)
    assert parsed.scheme == 'https'
    assert parsed.netloc == 'visualization.osdr.nasa.gov'
    assert parsed.path == '/radlab/api/'
    assert values['spacecraft'] == 'ISS'
    assert values['instrument_id'] == 'REM-Lid'
    assert values['timestamp>'] == '2023-01-01'
    assert values['timestamp<'] == '2023-01-02'
    assert values['absorbed_dose_rate'] == ''
    assert values['dose_equivalent_rate'] == ''
    assert values['flux'] == ''
    assert values['format'] == 'json'


@pytest.mark.parametrize('values', [
    {'startDate': '2023-02-30'},
    {'endDate': '2023-01-09'},
    {'instrument': 'DosTel&format=html'},
    {'quantities': 'dose'},
    {'url': 'https://attacker.invalid'},
])
def test_proxy_rejects_invalid_or_untrusted_query_parameters(values):
    with pytest.raises(ValueError):
        radlab_proxy.build_radlab_upstream_url(query(**values))


def test_fetch_uses_verified_tls_default_bounded_response_and_json_validation(monkeypatch):
    raw = json.dumps({'columns': ['timestamp'], 'index': [0], 'data': [['2023-01-01T00:00:00']]}).encode()
    response = io.BytesIO(raw)
    response.status = 200
    response.__enter__ = lambda self: self
    response.__exit__ = lambda *args: None
    monkeypatch.setattr(radlab_proxy, 'urlopen', lambda request, timeout: response)
    code, result = radlab_proxy.fetch_radlab(query())
    assert code == 200 and json.loads(result)['columns'] == ['timestamp']


def test_fetch_rejects_payload_larger_than_transfer_limit(monkeypatch):
    raw = b' ' * (radlab_proxy.MAX_RESPONSE_BYTES + 1)
    response = io.BytesIO(raw)
    response.status = 200
    response.__enter__ = lambda self: self
    response.__exit__ = lambda *args: None
    monkeypatch.setattr(radlab_proxy, 'urlopen', lambda request, timeout: response)
    with pytest.raises(ValueError, match='transfer limit'):
        radlab_proxy.fetch_radlab(query())
