"""Held-out documentary retrieval checks for ASTHRAL's local corpus."""
import argparse
import json
from time import perf_counter
from .offline_library import OfflineLibrary
from .vector_library import MiniLM, VectorLibrary

CASES = (
    ('Can a satisfied acid-base alternative make an absent bicarbonate redundant?', ('missing alternative', 'bicarbonate')),
    ('Does missing potassium still restrict insulin if the DKA criteria are satisfied?', ('potassium', 'independent')),
    ('Can a descriptive change in fitness alone establish recovery?', ('descriptive change', 'recovery')),
    ('Is it safe to reuse standing-test interpretations in free microgravity?', ('standing-test', 'microgravity')),
    ('Does a PCR trend itself establish reactivation?', ('pcr trend', 'reactivation')),
    ('Can a radiation interval total be read as lifetime dose?', ('interval total', 'lifetime dose')),
    ('Can supplementary public references change rules?', ('remote_unreviewed', 'update rules')),
    ('Does emergency priority depend on resources in anaphylaxis?', ('anaphylaxis', 'emergency')),
)

def run(manifest, index, embed):
    sparse = OfflineLibrary(manifest)
    dense = VectorLibrary(manifest, index, embed, lambda: 'FULL')
    result = {}
    for mode in ('lexical', 'vector', 'hybrid'):
        rows = []
        for question, required in CASES:
            start = perf_counter()
            blocks, _ = (sparse.search(question, 2) if mode == 'lexical'
                         else dense.retrieve(question, 2, mode))
            rows.append({'question': question, 'hits': [b['id'] for b in blocks],
                         'relevant_at_2': any(all(term in b['text'].lower() for term in required) for b in blocks),
                         'seconds': round(perf_counter()-start, 4)})
        result[mode] = {'hits_at_2': sum(row['relevant_at_2'] for row in rows), 'cases': rows}
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', required=True)
    p.add_argument('--index', required=True)
    p.add_argument('--url', required=True)
    p.add_argument('--digest', required=True)
    a = p.parse_args()
    print(json.dumps(run(a.manifest, a.index, MiniLM(a.url, a.digest)), indent=2))

if __name__ == '__main__':
    main()
