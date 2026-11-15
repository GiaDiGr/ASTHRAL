"""Exact cosine search over a bounded, verified scientific corpus."""
import argparse
from contextlib import closing
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
from urllib.parse import urlsplit
import httpx
from .knowledge_v08 import verified_blocks, search
from .offline_library import OfflineLibrary

DIMENSIONS = 384
FORMAT = 'ASTHRAL-SCIENCE-F32-1'
MODEL = 'all-minilm:l12-v2'
MAX_BLOCKS = 4096

def pack(values):
    if len(values) != DIMENSIONS or not all(math.isfinite(x) for x in values):
        raise ValueError('INVALID_EMBEDDING')
    norm = math.hypot(*values)
    if norm <= 0:
        raise ValueError('EMPTY_EMBEDDING')
    return struct.pack(f'<{DIMENSIONS}f', *(x / norm for x in values))

def unpack(raw):
    result = struct.unpack(f'<{DIMENSIONS}f', raw)
    if not math.isclose(math.hypot(*result), 1, abs_tol=1e-5):
        raise ValueError('INVALID_STORED_VECTOR')
    return result

class MiniLM:
    def __init__(self, url, digest):
        target = urlsplit(url)
        if (target.scheme != 'http' or target.hostname != '127.0.0.1' or not target.port
                or target.netloc != f'127.0.0.1:{target.port}' or target.path or target.query or target.fragment):
            raise ValueError('EMBEDDING_LOOPBACK_REQUIRED')
        if not re.fullmatch('[a-f0-9]{64}', digest):
            raise ValueError('EMBEDDING_DIGEST_REQUIRED')
        self.url = url
        self.identity = MODEL + '@' + digest
        self.digest = digest

    def __call__(self, texts):
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=20) as client:
            listing = client.get(self.url + '/api/tags')
            listing.raise_for_status()
            if not any(m['name'] == MODEL and m['digest'] == self.digest for m in listing.json()['models']):
                raise ValueError('EMBEDDING_MODEL_UNAVAILABLE')
            response = client.post(self.url + '/api/embed', json={
                'model': MODEL, 'input': texts, 'truncate': True, 'keep_alive': 0,
                'options': {'num_gpu': 0}})
            response.raise_for_status()
            return response.json()['embeddings']

def corpus(path):
    path = Path(path)
    if path.stat().st_size > 4_000_000:
        raise ValueError('LIBRARY_TOO_LARGE')
    manifest = json.loads(path.read_bytes())
    if manifest['schema_version'] != 2 or len(manifest['blocks']) > MAX_BLOCKS:
        raise ValueError('UNSUPPORTED_VECTOR_CORPUS')
    blocks, _, _ = verified_blocks(manifest)
    return manifest, blocks

def build(manifest_path, index, embed):
    manifest, blocks = corpus(manifest_path)
    if not blocks:
        raise ValueError('EMPTY_CORPUS')
    with closing(sqlite3.connect(index)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS metadata(format TEXT, model TEXT, corpus TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS vectors(id TEXT PRIMARY KEY, text TEXT, provenance TEXT, vector BLOB, checksum TEXT)')
        db.execute('DELETE FROM metadata')
        db.execute('DELETE FROM vectors')
        for i in range(0, len(blocks), 16):
            batch = blocks[i:i+16]
            vectors = embed([b['text'] for b in batch])
            if len(vectors) != len(batch):
                raise ValueError('EMBEDDING_COUNT_MISMATCH')
            for block, vector in zip(batch, vectors):
                raw = pack(vector)
                db.execute('INSERT INTO vectors VALUES (?,?,?,?,?)', (
                    block['id'], block['text'], json.dumps(block['reference'], sort_keys=True),
                    raw, sha256(raw).hexdigest()))
        db.execute('INSERT INTO metadata VALUES (?,?,?)', (FORMAT, embed.identity, manifest['sha256']))
    return len(blocks)

class VectorLibrary(OfflineLibrary):
    def __init__(self, path, index, embed, mode, hybrid=False):
        super().__init__(path)
        self.index = Path(index).resolve()
        self.embed = embed
        self.mode = mode
        self.hybrid = hybrid

    def retrieve(self, question, limit, ranking):
        manifest, verified = corpus(self.path)
        authoritative = {b['id']: b for b in verified}
        with closing(sqlite3.connect(self.index.as_uri() + '?mode=ro', uri=True)) as db:
            db.execute('BEGIN')
            metadata = db.execute('SELECT * FROM metadata LIMIT 2').fetchall()
            if metadata != [(FORMAT, self.embed.identity, manifest['sha256'])]:
                raise ValueError('VECTOR_INDEX_VERSION_MISMATCH')
            rows = db.execute('SELECT * FROM vectors LIMIT ?', (MAX_BLOCKS + 1,)).fetchall()
        if {r[0] for r in rows} != authoritative.keys() or len(rows) != len(authoritative):
            raise ValueError('VECTOR_INDEX_COVERAGE_MISMATCH')
        lexical, issues = search(manifest, question, 32)
        if ranking == 'hybrid' and not lexical:
            return [], issues
        candidates = {b['id']: i for i, b in enumerate(lexical, 1)}
        embeddings = self.embed([question])
        if len(embeddings) != 1:
            raise ValueError('QUERY_EMBEDDING_COUNT_MISMATCH')
        query = unpack(pack(embeddings[0]))
        scores = {}
        for identifier, text, reference, raw, checksum in rows:
            block = authoritative[identifier]
            if (text != block['text'] or json.loads(reference) != block['reference']
                    or sha256(raw).hexdigest() != checksum):
                raise ValueError('VECTOR_ROW_INTEGRITY_FAILED')
            vector = unpack(raw)
            if ranking == 'vector' or identifier in candidates:
                scores[identifier] = math.fsum(a*b for a, b in zip(query, vector))
        ordered = sorted(scores, key=lambda key: (-scores[key], key))
        if ranking == 'hybrid':
            semantic = {key: i for i, key in enumerate(ordered, 1)}
            ordered.sort(key=lambda key: (-(1/(60+candidates[key]) + 1/(60+semantic[key])), key))
        return [{**authoritative[key], 'retrieval_score': round(scores[key], 6),
                 'retrieval_algorithm': 'LEXICAL_GATED_RRF_1' if ranking == 'hybrid' else 'COSINE_1'}
                for key in ordered[:limit]], issues

    def search(self, question, limit=2):
        if not self.hybrid or self.mode() != 'FULL':
            return super().search(question, limit)
        try:
            return self.retrieve(question, limit, 'hybrid')
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, httpx.HTTPError, struct.error, MemoryError):
            blocks, issues = super().search(question, limit)
            return blocks, [*issues, 'VECTOR_UNAVAILABLE_LEXICAL_FALLBACK']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--index', required=True)
    parser.add_argument('--url', default='http://127.0.0.1:11434')
    parser.add_argument('--digest', required=True)
    args = parser.parse_args()
    print(f'Indexed {build(args.manifest, args.index, MiniLM(args.url, args.digest))} verified chunks')

if __name__ == '__main__':
    main()
