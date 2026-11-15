import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ANATOMY_MODEL, ANATOMY_REGIONS, anatomyRegionMatches, regionForAnatomyName,
} from '../src/anatomy-view.js';

test('anatomy region identifiers are stable, unique and include laterality', () => {
  const ids = ANATOMY_REGIONS.map(item => item.id);
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(ids.includes('left_eye') && ids.includes('right_eye'));
  assert.ok(ids.includes('left_shoulder') && ids.includes('right_shoulder'));
  assert.ok(ids.includes('left_foot') && ids.includes('right_foot'));
});

test('source mesh labels map to an explicit region while unknown tissues remain unmapped', () => {
  assert.equal(regionForAnatomyName('Lateral rectus muscle.l')?.id, 'left_eye');
  assert.equal(regionForAnatomyName('Lateral rectus muscle.r')?.id, 'right_eye');
  assert.equal(regionForAnatomyName('Biceps brachii.l')?.id, 'left_upper_arm');
  assert.equal(regionForAnatomyName('Biceps brachii.r')?.id, 'right_upper_arm');
  assert.equal(regionForAnatomyName('Rectus abdominis')?.id, 'abdomen');
  assert.equal(regionForAnatomyName('unrecognized mesh'), null);
  assert.equal(anatomyRegionMatches('left_upper_arm', 'Biceps brachii.l'), true);
  assert.equal(anatomyRegionMatches('right_upper_arm', 'Biceps brachii.l'), false);
});

test('anatomy attribution identifies the licensed model layer and prohibits clinical claims', () => {
  assert.equal(ANATOMY_MODEL.clinical_validation, false);
  assert.equal(ANATOMY_MODEL.license, 'CC BY-SA 4.0 (model layer; derived from BodyParts3D CC BY-SA 2.1 Japan)');
  assert.equal(ANATOMY_MODEL.sha256, 'f8399ba12dedb7cd88de199eddf7e3f8a3de8373a69228fb9da7ce1b7981ffd2');
});
