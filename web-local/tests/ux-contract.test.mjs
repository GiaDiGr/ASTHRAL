import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const html=await readFile(new URL('../src/index.html',import.meta.url),'utf8');
const experience=await readFile(new URL('../src/experience.js',import.meta.url),'utf8');
const css=await readFile(new URL('../src/style.css',import.meta.url),'utf8');
test('default local sign-in exposes only email and password and demo follows authentication',()=>{
  const form=html.match(/<form id="signin-form">([\s\S]*?)<\/form>/)?.[1]??'';
  assert.deepEqual([...form.matchAll(/<input\b/g)].map(()=>1),[1,1]);
  assert.match(form,/<input id="signin-email" type="email"[^>]*autocomplete="username"/);
  assert.match(form,/<input id="signin-password" type="password"[^>]*autocomplete="current-password"/);
  assert.ok(html.indexOf('id="signin-form"')<html.indexOf('id="create-form"'));
  assert.ok(html.indexOf('id="create-form"')<html.indexOf('id="demo-title"'));
  assert.match(html,/<form id="create-form" hidden>/);
  assert.match(html,/No account required\./);
});
test('focused workspace routes expose the core tasks and all contributed vision modules',()=>{
  for(const id of ['dashboard','clinical','assistant','history','vision','voice','knowledge','settings']) assert.match(html,new RegExp(`id="${id}"`));
  for(const id of ['monitoring','followup','inventory','mission-context','management-history']) assert.match(experience,new RegExp(`id='${id}'`));
  for(const module of ['OcularVision','MotionGuard','SkinGuard','EchoVision']) assert.ok(html.includes(module));
  assert.match(html,/no SANS diagnosis/i);
  assert.match(html,/Disabled[\s\S]*EchoVision/);
});
test('mobile core navigation keeps History reachable at narrow widths',()=>{
  assert.match(html,/<a href="#history" data-view="history">History<\/a>/);
  assert.doesNotMatch(css,/\.side-rail nav>a:nth-of-type\(5\)\{display:none\}/);
  assert.match(css,/\.side-rail nav>a\{font-size:10px;min-width:0;overflow-wrap:anywhere\}/);
});
