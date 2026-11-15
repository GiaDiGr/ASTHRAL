"""Narrow same-origin proxy for public NASA RadLab GET queries in the local preview."""
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlsplit
from urllib.request import Request, urlopen
import json
import re

RADLAB_API = 'https://visualization.osdr.nasa.gov/radlab/api/'
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_WINDOW_DAYS = 7
QUANTITIES = {'absorbed_dose_rate', 'dose_equivalent_rate', 'flux'}
FIELDS = ('instrument', 'instrument_family', 'instrument_id', 'module', 'latitude', 'longitude', 'altitude', 'B', 'L')
SAFE_FILTER = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 ._/-]{0,79}$')


def build_radlab_upstream_url(query_string: str) -> str:
    query = parse_qs(query_string, keep_blank_values=True, strict_parsing=True)
    allowed = {'startDate', 'endDate', 'quantities', 'spacecraft', 'instrument', 'instrumentId'}
    if set(query) - allowed or any(len(values) != 1 for values in query.values()):
        raise ValueError('Unsupported or repeated RadLab proxy parameter.')
    start, end = query.get('startDate', [''])[0], query.get('endDate', [''])[0]
    try:
        start_dt = datetime.strptime(start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError('Choose valid RadLab observation dates in UTC order.') from exc
    if start_dt.strftime('%Y-%m-%d') != start or end_dt.strftime('%Y-%m-%d') != end or end_dt < start_dt:
        raise ValueError('Choose valid RadLab observation dates in UTC order.')
    if (end_dt - start_dt).days + 1 > MAX_WINDOW_DAYS:
        raise ValueError(f'RadLab queries are limited to {MAX_WINDOW_DAYS} days per request.')
    quantities = query.get('quantities', [''])[0].split(',')
    if not quantities or any(item not in QUANTITIES for item in quantities) or len(set(quantities)) != len(quantities):
        raise ValueError('Choose one or more documented RadLab quantities.')
    values = {key: query.get(key, [''])[0] for key in ('spacecraft', 'instrument', 'instrumentId')}
    for value in values.values():
        if value and not SAFE_FILTER.fullmatch(value):
            raise ValueError('RadLab filter contains unsupported characters.')
    pairs = []
    if values['spacecraft']:
        pairs.append(('spacecraft', values['spacecraft']))
    if values['instrument']:
        pairs.append(('instrument', values['instrument']))
    if values['instrumentId']:
        pairs.append(('instrument_id', values['instrumentId']))
    end_exclusive = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    encoded = [(key, value) for key, value in pairs]
    result = [(quote(key, safe=''), quote(value, safe='')) for key, value in encoded]
    result.extend([('timestamp%3E', quote(start, safe='')), ('timestamp%3C', quote(end_exclusive, safe=''))])
    for field in (*FIELDS, *sorted(QUANTITIES)):
        if field in QUANTITIES and field not in quantities:
            continue
        if field == 'instrument' and values['instrument']:
            continue
        if field == 'instrument_id' and values['instrumentId']:
            continue
        result.append((quote(field, safe=''), ''))
    result.append(('format', 'json'))
    return RADLAB_API + '?' + '&'.join(f'{key}={value}' for key, value in result)


def fetch_radlab(query_string: str) -> tuple[int, bytes]:
    url = build_radlab_upstream_url(query_string)
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'ASTHRAL-RadLab-Proxy/1.0'})
    try:
        with urlopen(request, timeout=25) as response:
            if response.status != 200:
                raise ValueError(f'NASA RadLab returned HTTP {response.status}.')
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            if len(payload) > MAX_RESPONSE_BYTES:
                raise ValueError('NASA RadLab response exceeds the ASTHRAL transfer limit.')
            json.loads(payload)
            return 200, payload
    except HTTPError as exc:
        raise ValueError(f'NASA RadLab returned HTTP {exc.code}.') from exc
    except URLError as exc:
        raise ConnectionError('NASA RadLab is unavailable from this connection.') from exc
