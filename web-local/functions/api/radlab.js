import { buildRadLabUpstreamUrl, normalizeRadLabResponse, RADLAB_MAX_RESPONSE_BYTES } from '../../src/radlab.js';

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  },
});

async function boundedBody(response) {
  const reader = response.body?.getReader();
  if (!reader) {
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.byteLength > RADLAB_MAX_RESPONSE_BYTES) throw Error('NASA RadLab response exceeds the ASTHRAL transfer limit.');
    return bytes;
  }
  const chunks = [];
  let size = 0;
  let complete = false;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) { complete = true; break; }
      size += value.byteLength;
      if (size > RADLAB_MAX_RESPONSE_BYTES) throw Error('NASA RadLab response exceeds the ASTHRAL transfer limit.');
      chunks.push(value);
    }
  } finally {
    if (!complete) await reader.cancel().catch(() => {});
    reader.releaseLock?.();
  }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.byteLength; }
  return result;
}

export async function onRequest({ request }) {
  if (request.method !== 'GET') return json({ error: 'RadLab proxy accepts GET requests only.' }, 405);
  const pageUrl = new URL(request.url);
  const origin = request.headers.get('Origin');
  if (origin && origin !== pageUrl.origin) return json({ error: 'Cross-origin RadLab proxy requests are not accepted.' }, 403);
  try {
    const query = pageUrl.searchParams;
    const allowed = new Set(['startDate', 'endDate', 'quantities', 'spacecraft', 'instrument', 'instrumentId']);
    if ([...query.keys()].some(key => !allowed.has(key))) throw Error('Unsupported RadLab proxy parameter.');
    const values = key => query.getAll(key);
    for (const key of allowed) if (values(key).length > 1) throw Error('Repeated RadLab parameters are not accepted.');
    const quantityValue = query.get('quantities');
    const filters = {
      startDate: query.get('startDate'),
      endDate: query.get('endDate'),
      quantities: quantityValue?.split(',') ?? [],
      spacecraft: query.get('spacecraft') ?? '',
      instrument: query.get('instrument') ?? '',
      instrumentId: query.get('instrumentId') ?? '',
    };
    const upstreamUrl = buildRadLabUpstreamUrl(filters);
    const upstream = await fetch(upstreamUrl, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      // Cloudflare Workers support `follow` and `manual`, but not `error`.
      // Manual mode preserves the fixed-upstream boundary; reject every 3xx below.
      redirect: 'manual',
      signal: request.signal,
    });
    if (upstream.status >= 300 && upstream.status < 400) {
      return json({ error: 'NASA RadLab redirect responses are not accepted.', provider: 'NASA_OSDR_RADLAB' }, 502);
    }
    if (!upstream.ok) return json({ error: `NASA RadLab returned HTTP ${upstream.status}.`, provider: 'NASA_OSDR_RADLAB' }, 502);
    const bytes = await boundedBody(upstream);
    const payload = JSON.parse(new TextDecoder().decode(bytes));
    const snapshot = normalizeRadLabResponse(payload, { requested: filters });
    const serialized = JSON.stringify(snapshot);
    if (new TextEncoder().encode(serialized).byteLength > RADLAB_MAX_RESPONSE_BYTES) throw Error('Normalized NASA RadLab response exceeds the ASTHRAL transfer limit.');
    return new Response(serialized, {
      status: 200,
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
        'X-ASTHRAL-Source': 'NASA_OSDR_RADLAB',
      },
    });
  } catch (error) {
    const message = typeof error?.message === 'string' ? error.message.slice(0, 240) : 'RadLab query failed.';
    const status = /valid|choose|limited|unsupported|repeated|contains unsupported/i.test(message) ? 400 : 502;
    return json({ error: message, provider: 'NASA_OSDR_RADLAB' }, status);
  }
}
