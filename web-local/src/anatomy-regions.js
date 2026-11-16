/**
 * Stable body-map contract. These IDs identify orientation regions only;
 * they do not localize physiological findings or support diagnosis.
 */
export const ANATOMY_REGIONS = Object.freeze([
  ['head', 'Head', 'External anatomy', 'midline'],
  ['face', 'Face', 'External anatomy', 'midline'],
  ['left_eye', 'Left eye region', 'External anatomy', 'left'],
  ['right_eye', 'Right eye region', 'External anatomy', 'right'],
  ['neck', 'Neck', 'External anatomy', 'midline'],
  ['chest', 'Chest', 'External anatomy', 'midline'],
  ['abdomen', 'Abdomen', 'External anatomy', 'midline'],
  ['back', 'Back', 'External anatomy', 'midline'],
  ['left_shoulder', 'Left shoulder', 'External anatomy', 'left'],
  ['right_shoulder', 'Right shoulder', 'External anatomy', 'right'],
  ['left_upper_arm', 'Left upper arm', 'External anatomy', 'left'],
  ['right_upper_arm', 'Right upper arm', 'External anatomy', 'right'],
  ['left_forearm', 'Left forearm', 'External anatomy', 'left'],
  ['right_forearm', 'Right forearm', 'External anatomy', 'right'],
  ['left_hand', 'Left hand', 'External anatomy', 'left'],
  ['right_hand', 'Right hand', 'External anatomy', 'right'],
  ['left_hip', 'Left hip', 'External anatomy', 'left'],
  ['right_hip', 'Right hip', 'External anatomy', 'right'],
  ['left_thigh', 'Left thigh', 'External anatomy', 'left'],
  ['right_thigh', 'Right thigh', 'External anatomy', 'right'],
  ['left_knee', 'Left knee', 'External anatomy', 'left'],
  ['right_knee', 'Right knee', 'External anatomy', 'right'],
  ['left_lower_leg', 'Left lower leg', 'External anatomy', 'left'],
  ['right_lower_leg', 'Right lower leg', 'External anatomy', 'right'],
  ['left_ankle', 'Left ankle', 'External anatomy', 'left'],
  ['right_ankle', 'Right ankle', 'External anatomy', 'right'],
  ['left_foot', 'Left foot', 'External anatomy', 'left'],
  ['right_foot', 'Right foot', 'External anatomy', 'right'],
].map(([id, label, system, laterality]) => Object.freeze({ id, label, system, laterality })));

export const ANATOMY_MODEL = Object.freeze({
  name: 'MakeHuman smooth external body base mesh (male morphology)',
  source: 'https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89',
  asset: './vendor/anatomy/makehuman-external-body.glb',
  license: 'CC0 1.0',
  sha256: '86c7cdfa989924b45e2e5110c131a4a4e6251ceb4e71246be68e468f3a32ca86',
  source_triangles: 109064,
  stated_dimensions_cm: Object.freeze({ width: 119, depth: 49, height: 179 }),
  clinical_validation: false,
  attribution: 'Innerscene adaptation of MakeHuman CC0 assets; see source page and attribution file.',
});

const BONE_SEMANTICS = Object.create(null);
const assign = (semantic, names) => { for (const name of names) BONE_SEMANTICS[name] = semantic; };

assign('head', ['head']);
assign('neck', ['neck01', 'neck02', 'neck03']);
assign('trunk', ['spine01', 'spine02', 'spine03', 'spine04', 'spine05', 'breastL', 'breastR']);
assign('hip', ['pelvisL', 'pelvisR']);
assign('face', [
  'jaw', 'special04', 'oris01', 'oris02', 'oris03L', 'oris03R', 'oris04L', 'oris04R',
  'oris05', 'oris06', 'oris06L', 'oris06R', 'oris07L', 'oris07R', 'tongue00', 'tongue01',
  'tongue02', 'tongue03', 'tongue04', 'tongue05L', 'tongue05R', 'tongue06L', 'tongue06R',
  'tongue07L', 'tongue07R', 'levator02L', 'levator03L', 'levator04L', 'levator05L',
  'levator02R', 'levator03R', 'levator04R', 'levator05R', 'special01', 'special03',
  'levator06L', 'levator06R', 'special05L', 'special05R', 'special06L', 'special06R',
  'temporalis01L', 'temporalis01R', 'temporalis02L', 'temporalis02R',
  'risorius02L', 'risorius02R', 'risorius03L', 'risorius03R',
]);
assign('left_eye', ['eyeL', 'orbicularis03L', 'orbicularis04L', 'oculi01L', 'oculi02L']);
assign('right_eye', ['eyeR', 'orbicularis03R', 'orbicularis04R', 'oculi01R', 'oculi02R']);

for (const [suffix, side] of [['L', 'left'], ['R', 'right']]) {
  assign(side + '_shoulder', ['clavicle' + suffix, 'shoulder01' + suffix]);
  assign(side + '_upper_arm', ['upperarm01' + suffix, 'upperarm02' + suffix]);
  assign(side + '_forearm', ['lowerarm01' + suffix, 'lowerarm02' + suffix]);
  assign(side + '_hand', ['wrist' + suffix, 'metacarpal1' + suffix, 'metacarpal2' + suffix, 'metacarpal3' + suffix, 'metacarpal4' + suffix]);
  for (let finger = 1; finger <= 5; finger++) {
    for (let segment = 1; segment <= 3; segment++) assign(side + '_hand', ['finger' + finger + '-' + segment + suffix]);
  }
  assign(side + '_thigh', ['upperleg01' + suffix, 'upperleg02' + suffix]);
  assign(side + '_knee', ['lowerleg01' + suffix]);
  assign(side + '_lower_leg', ['lowerleg02' + suffix]);
  assign(side + '_ankle', ['foot' + suffix]);
  for (let toe = 1; toe <= 5; toe++) {
    for (let segment = 1; segment <= (toe === 1 ? 2 : 3); segment++) assign(side + '_foot', ['toe' + toe + '-' + segment + suffix]);
  }
}

export function regionIdFromBoneName(name) {
  return BONE_SEMANTICS[String(name ?? '')] ?? null;
}

function regionForHead(point) {
  const { x, y, z } = point;
  if (z > 0.075 && y >= 1.57 && y <= 1.76) {
    if (y >= 1.65 && y <= 1.71 && Math.abs(x) >= 0.014 && Math.abs(x) <= 0.055 && z > 0.105) {
      return x > 0 ? 'left_eye' : 'right_eye';
    }
    return 'face';
  }
  return 'head';
}

function regionForTrunk(point) {
  if (point.y < 0.88 || point.y > 1.52) return null;
  if (point.z < 0) return 'back';
  return point.y < 1.13 ? 'abdomen' : 'chest';
}

/**
 * Resolve the visible skin point from explicit MakeHuman bone influences and
 * source-model surface landmarks. No name regexes or first-match fallback.
 * weightedBones is an array of [boneName, weight] pairs.
 */
export function resolveAnatomySurfaceRegion(point, weightedBones) {
  if (![point?.x, point?.y, point?.z].every(Number.isFinite) || !Array.isArray(weightedBones)) return null;
  const scores = new Map();
  for (const [name, rawWeight] of weightedBones) {
    const semantic = regionIdFromBoneName(name);
    const weight = Number(rawWeight);
    if (!semantic || !Number.isFinite(weight) || weight <= 0) continue;
    scores.set(semantic, (scores.get(semantic) ?? 0) + weight);
  }
  const ranked = [...scores].sort((a, b) => b[1] - a[1]);
  if (!ranked.length || ranked[0][1] < 0.18) return null;
  if (ranked.length > 1 && ranked[0][1] - ranked[1][1] < Math.max(0.035, ranked[0][1] * 0.08)) return null;
  const [semantic] = ranked[0];
  if (semantic === 'head') return regionForHead(point);
  if (semantic === 'trunk') return regionForTrunk(point);
  if (semantic === 'hip') return point.x > 0 ? 'left_hip' : point.x < 0 ? 'right_hip' : null;
  if (semantic === 'left_knee' || semantic === 'right_knee') {
    if (point.y < 0.44) return semantic.replace('_knee', '_lower_leg');
    return semantic;
  }
  if (semantic === 'left_lower_leg' || semantic === 'right_lower_leg') {
    if (point.y < 0.24) return semantic.replace('_lower_leg', '_ankle');
    return semantic;
  }
  if (semantic === 'left_ankle' || semantic === 'right_ankle') {
    return point.y < 0.14 ? semantic.replace('_ankle', '_foot') : semantic;
  }
  return ANATOMY_REGIONS.some(region => region.id === semantic) ? semantic : null;
}

export function regionForAnatomyName(name) {
  const semantic = regionIdFromBoneName(name);
  if (!semantic || ['trunk', 'hip', 'head'].includes(semantic)) return null;
  return ANATOMY_REGIONS.find(region => region.id === semantic) ?? null;
}

export function anatomyRegionMatches(regionId, boneName) {
  return regionForAnatomyName(boneName)?.id === regionId;
}
