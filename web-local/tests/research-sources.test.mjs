import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeSourceRegistry} from '../src/research-sources.js';

test('offline bibliography exposes bounded official NASA and USDA references only',()=>{
 const source={source_id:'NASA-1',institution:'NASA',title:'Evidence report',publication_date:'2026',url:'https://humanresearchroadmap.nasa.gov/evidence/',evidence_category:'CATALOGUE',reuse_status:'LINK_ONLY'};
 const usda={...source,source_id:'USDA-1',institution:'USDA',title:'Food composition data',url:'https://fdc.nal.usda.gov/download-datasets/'};
 const registry=normalizeSourceRegistry({schema_version:'1.0.0',reviewed_at:'2026-11-15',sources:[source,usda,{...source,source_id:'evil',url:'https://example.org/'},{...source,source_id:'credential',url:'https://user:secret@nasa.gov/path'}]});
 assert.equal(registry.sources.length,2);assert.deepEqual(registry.sources.map(x=>x.source_id),['NASA-1','USDA-1']);
});

test('malformed registry fails closed and duplicate source IDs are not repeated',()=>{
 const source={source_id:'NASA-1',institution:'NASA',title:'Report',publication_date:'2026',url:'https://nasa.gov/report',evidence_category:'REPORT',reuse_status:'LINK_ONLY'};
 assert.equal(normalizeSourceRegistry({schema_version:'1.0.0',sources:[source,source]}).sources.length,1);
 assert.throws(()=>normalizeSourceRegistry({schema_version:'1',sources:[source]}),/Invalid local source registry/);
});
