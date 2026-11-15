import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeSourceRegistry} from '../src/research-sources.js';

test('offline bibliography exposes bounded official NASA references only',()=>{
 const source={source_id:'NASA-1',institution:'NASA',title:'Evidence report',publication_date:'2026',url:'https://humanresearchroadmap.nasa.gov/evidence/',evidence_category:'CATALOGUE',reuse_status:'LINK_ONLY'};
 const registry=normalizeSourceRegistry({schema_version:'1.0.0',reviewed_at:'2026-11-15',sources:[source,{...source,source_id:'evil',url:'https://example.org/'},{...source,source_id:'credential',url:'https://user:secret@nasa.gov/path'}]});
 assert.equal(registry.sources.length,1);assert.equal(registry.sources[0].source_id,'NASA-1');
});

test('malformed registry fails closed and duplicate source IDs are not repeated',()=>{
 const source={source_id:'NASA-1',institution:'NASA',title:'Report',publication_date:'2026',url:'https://nasa.gov/report',evidence_category:'REPORT',reuse_status:'LINK_ONLY'};
 assert.equal(normalizeSourceRegistry({schema_version:'1.0.0',sources:[source,source]}).sources.length,1);
 assert.throws(()=>normalizeSourceRegistry({schema_version:'1',sources:[source]}),/Invalid local source registry/);
});
