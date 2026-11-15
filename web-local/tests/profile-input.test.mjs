import test from 'node:test';
import assert from 'node:assert/strict';
import {initialClinicalInput,criterionInputConcepts} from '../src/profile-input.js';
test('an empty persistent profile cannot inherit a synthetic diagnostic scenario',()=>{
 const value=initialClinicalInput([],'synthetic-profile');assert.deepEqual(value.request.observations,[]);assert.deepEqual(value.request.measurement_bindings,[]);assert.equal(value.request.population,'UNKNOWN');assert.equal(value.request.age_years,null);assert.equal(value.request.as_of,null);assert.equal(value.request.window_start,null);assert.deepEqual(value.request.resources,{});
});
test('saved inputs remain historical, owner-bound and independent from the view draft',()=>{
 const row={subject_id:'synthetic-profile',snapshot:{request:{subject_id:'synthetic-profile',mission_id:'browser-mission',as_of:'2026-10-16T12:00:00Z',observations:[{concept:'synthetic',value:82}]},mission:{id:'browser-mission'}}};
 const value=initialClinicalInput([row],'synthetic-profile');assert.equal(value.request.as_of,row.snapshot.request.as_of);value.request.observations[0].value=999;assert.equal(row.snapshot.request.observations[0].value,82);
 assert.throws(()=>initialClinicalInput([row],'another-profile'),/SCOPE_MISMATCH/);
});

test('special confirmation paths and nested OR branches expose original supported input names',()=>{
 const logic={qualifying_paths:[{all_of:[{field:'a1c_percent'},{field:'assay_quality.a1c_valid'}]},{any_of:[{field:'fasting_plasma_glucose_mg_dl'},{field:'fasting_hours'}]}]};
 const supported=['a1c_percent','assay_quality.a1c_valid','fasting_plasma_glucose_mg_dl','fasting_hours'];assert.deepEqual(criterionInputConcepts(logic,{},supported),supported);
});
test('derived criteria offer original raw dependencies and never editable derived results',()=>{
 const logic={any_of:[{derived_field:'delta_sbp_mm_hg'},{derived_field:'delta_dbp_mm_hg'}]},dependencies={delta_sbp_mm_hg:['baseline_sbp_mm_hg','upright_sbp_mm_hg'],delta_dbp_mm_hg:['baseline_dbp_mm_hg','upright_dbp_mm_hg']};
 const raw=Object.values(dependencies).flat();assert.deepEqual(criterionInputConcepts(logic,dependencies,raw),raw);assert.deepEqual(criterionInputConcepts({derived_field:'unreviewed'},dependencies,raw),[]);
});
