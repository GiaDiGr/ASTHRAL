import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  ANATOMY_MODEL, ANATOMY_REGIONS, anatomyRegionMatches, regionForAnatomyName,
  regionIdFromBoneName, resolveAnatomySurfaceRegion,
} from '../src/anatomy-view.js';

const point = (x, y, z) => ({ x, y, z });
const oneBone = (name, weight = 1) => [[name, weight]];

test('the stable surface contract includes all 28 required IDs, with unique laterality pairs', () => {
  const ids = ANATOMY_REGIONS.map(item => item.id);
  assert.equal(ids.length, 28);
  assert.equal(new Set(ids).size, ids.length);
  for (const id of [
    'head', 'face', 'left_eye', 'right_eye', 'neck', 'chest', 'abdomen', 'back',
    'left_shoulder', 'right_shoulder', 'left_upper_arm', 'right_upper_arm',
    'left_forearm', 'right_forearm', 'left_hand', 'right_hand', 'left_hip', 'right_hip',
    'left_thigh', 'right_thigh', 'left_knee', 'right_knee', 'left_lower_leg', 'right_lower_leg',
    'left_ankle', 'right_ankle', 'left_foot', 'right_foot',
  ]) assert.ok(ids.includes(id), 'missing stable region ID: ' + id);
});

test('bone mapping uses exact source-model identifiers rather than muscle-name pattern guessing', () => {
  assert.equal(regionIdFromBoneName('upperarm01L'), 'left_upper_arm');
  assert.equal(regionIdFromBoneName('upperarm01R'), 'right_upper_arm');
  assert.equal(regionForAnatomyName('oculi01L')?.id, 'left_eye');
  assert.equal(anatomyRegionMatches('right_upper_arm', 'upperarm01R'), true);
  assert.equal(anatomyRegionMatches('left_upper_arm', 'upperarm01R'), false);
  for (const legacyOrUnknown of ['Biceps brachii.l', 'left_deltoid', 'unrecognized mesh', '']) {
    assert.equal(regionForAnatomyName(legacyOrUnknown), null);
    assert.equal(regionIdFromBoneName(legacyOrUnknown), null);
  }
});

test('head, face and paired eye zones are resolved from the visible model surface', () => {
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.74, 0.03), oneBone('head')), 'head');
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.64, 0.13), oneBone('head')), 'face');
  assert.equal(resolveAnatomySurfaceRegion(point(0.03, 1.68, 0.15), oneBone('head')), 'left_eye');
  assert.equal(resolveAnatomySurfaceRegion(point(-0.03, 1.68, 0.15), oneBone('head')), 'right_eye');
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.64, 0.13), oneBone('oculi01L')), 'left_eye');
});

test('chest, abdomen and back split the trunk using source-model surface landmarks', () => {
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.28, 0.12), oneBone('spine02')), 'chest');
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.03, 0.12), oneBone('spine05')), 'abdomen');
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.25, -0.10), oneBone('spine03')), 'back');
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.60, 0.12), oneBone('spine01')), null);
});

test('explicit limbs preserve left/right laterality and give joints separate surface regions', () => {
  assert.equal(resolveAnatomySurfaceRegion(point(0.23, 1.40, 0.04), oneBone('upperarm01L')), 'left_upper_arm');
  assert.equal(resolveAnatomySurfaceRegion(point(-0.23, 1.40, 0.04), oneBone('upperarm01R')), 'right_upper_arm');
  assert.equal(resolveAnatomySurfaceRegion(point(0.39, 1.22, 0.04), oneBone('lowerarm01L')), 'left_forearm');
  assert.equal(resolveAnatomySurfaceRegion(point(0.55, 1.04, 0.18), oneBone('wristL')), 'left_hand');
  assert.equal(resolveAnatomySurfaceRegion(point(-0.55, 1.04, 0.18), oneBone('wristR')), 'right_hand');
  assert.equal(resolveAnatomySurfaceRegion(point(0.15, 0.94, 0), oneBone('pelvisL')), 'left_hip');
  assert.equal(resolveAnatomySurfaceRegion(point(-0.15, 0.94, 0), oneBone('pelvisR')), 'right_hip');
  assert.equal(resolveAnatomySurfaceRegion(point(0.14, 0.72, 0), oneBone('upperleg01L')), 'left_thigh');
  assert.equal(resolveAnatomySurfaceRegion(point(0.15, 0.52, 0), oneBone('lowerleg01L')), 'left_knee');
  assert.equal(resolveAnatomySurfaceRegion(point(0.16, 0.38, 0), oneBone('lowerleg01L')), 'left_lower_leg');
  assert.equal(resolveAnatomySurfaceRegion(point(0.19, 0.20, 0), oneBone('lowerleg02L')), 'left_ankle');
  assert.equal(resolveAnatomySurfaceRegion(point(0.20, 0.12, 0.10), oneBone('footL')), 'left_foot');
  assert.equal(resolveAnatomySurfaceRegion(point(-0.20, 0.20, 0), oneBone('lowerleg02R')), 'right_ankle');
  assert.equal(resolveAnatomySurfaceRegion(point(-0.20, 0.12, 0.10), oneBone('footR')), 'right_foot');
});

test('ambiguous, insufficient and conflicting surface evidence returns no region instead of guessing', () => {
  assert.equal(resolveAnatomySurfaceRegion(point(0.2, 1.4, 0), []), null);
  assert.equal(resolveAnatomySurfaceRegion(point(0.2, 1.4, 0), oneBone('unknownBone')), null);
  assert.equal(resolveAnatomySurfaceRegion(point(0.2, 1.4, 0), [['upperarm01L', 0.5], ['lowerarm01L', 0.5]]), null);
  assert.equal(resolveAnatomySurfaceRegion(point(0, 0.94, 0), oneBone('pelvisL')), null);
  assert.equal(resolveAnatomySurfaceRegion(point(0, 1.8, 0), oneBone('spine01')), null);
});

test('the licensed external model asset and manifest match their recorded bytes and hash', () => {
  const assetPath = resolve('src/vendor/anatomy/makehuman-external-body.glb');
  const manifestPath = resolve('src/vendor/anatomy/model-manifest.json');
  const asset = readFileSync(assetPath);
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  assert.equal(asset.length, 4498248);
  assert.equal(createHash('sha256').update(asset).digest('hex'), ANATOMY_MODEL.sha256);
  assert.equal(manifest.asset, 'makehuman-external-body.glb');
  assert.equal(manifest.sha256, ANATOMY_MODEL.sha256);
  assert.equal(ANATOMY_MODEL.license, 'CC0 1.0');
  assert.equal(ANATOMY_MODEL.clinical_validation, false);
  assert.equal(ANATOMY_MODEL.source_triangles, 109064);
  assert.ok(existsSync(resolve('src/vendor/anatomy/zanatomy-muscles.glb')), 'retain legacy source asset');
});
