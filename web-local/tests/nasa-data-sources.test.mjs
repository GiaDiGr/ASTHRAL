import test from 'node:test';
import assert from 'node:assert/strict';
import { getNasaDataSource, NASA_DATA_SOURCES } from '../src/nasa-data-sources.js';

test('reviewed NASA source registry separates integrated and reference-only interfaces', () => {
  assert.equal(new Set(NASA_DATA_SOURCES.map(source => source.id)).size, NASA_DATA_SOURCES.length);
  assert.deepEqual(NASA_DATA_SOURCES.map(source => source.id), [
    'NASA_OSDR_RADLAB', 'NASA_CCMC_DONKI', 'NASA_OSDR_BIODATA', 'NASA_OSDR_EDA',
  ]);
  assert.equal(getNasaDataSource('NASA_OSDR_RADLAB').endpoint, 'https://visualization.osdr.nasa.gov/radlab/api/');
  assert.equal(getNasaDataSource('NASA_OSDR_RADLAB').units.absorbed_dose_rate, 'μGy/h');
  assert.match(getNasaDataSource('NASA_OSDR_RADLAB').cache, /Network responses: no-store/);
  assert.match(getNasaDataSource('NASA_OSDR_BIODATA').test_status, /NOT CONNECTED TO CLINICAL EVALUATION/);
  assert.match(getNasaDataSource('NASA_OSDR_EDA').test_status, /EVALUATED_NOT_INTEGRATED/);
  assert.equal(getNasaDataSource('NASA_OSDR_EDA').cache, 'No ASTHRAL integration or local cache.');
  assert.equal(getNasaDataSource('UNKNOWN'), null);
});
