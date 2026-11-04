// Real production assets executed against a simulated DOM, NOT a real browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const frames=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),web=path.join(__dirname,'../vigile/web');
let passed=0;
function harness(data,evalId){
 const nodes={},nav=[];class N{
  constructor(tag,text=''){this.tag=tag;this._text=String(text);this.children=[];this.dataset={};this.attrs={};this.value='';this.hidden=false;this.parentElement=null;}
  set id(v){this._id=v;nodes[v]=this;}get id(){return this._id;}
  set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join(' ');}
  append(...items){for(const n of items){n.parentElement=this;this.children.push(n);if(this.tag==='select'&&!this.value)this.value=n.value;}}
  replaceChildren(...items){this.children=[];this._text='';this.append(...items);}
  setAttribute(k,v){this.attrs[k]=String(v);}getAttribute(k){return this.attrs[k];}
  get options(){return this.children;}remove(){if(this.id)delete nodes[this.id];if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(x=>x!==this);}
  after(n){this.parentElement?.append(n);}
 }
 const html=fs.readFileSync(path.join(web,'index.html'),'utf8');for(const match of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"/g)){const n=new N(match[1]);n.id=match[2];}
 for(const view of ['general','monitoring','clinical','followup','assistant']){const n=new N('button');n.dataset.view=view;nav.push(n);}
 const context={document:{getElementById:id=>nodes[id]||null,createElement:tag=>new N(tag),createElementNS:(_,tag)=>new N(tag),querySelectorAll:q=>q==='[data-view]'?nav:[]},fetch:async()=>{throw Error('Network disabled in simulated DOM');},setInterval:()=>{},location:{reload(){}},console,Intl,Date,Number,Set,JSON,Object,URLSearchParams};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(web,'app.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(web,'management.js'),'utf8'),context);
 context.fixture=structuredClone(data);context.frameIndex=frames.index;context.eid=evalId||Object.values(data.monitoring.at(-1).clinical_evaluations||{})[0]?.id||'';
 vm.runInContext("dashboard=fixture;missionFrames=frameIndex;selectedCycleId=dashboard.monitoring.at(-1).id;$('mission-frame').value=dashboard.historical_frame.id;$('evaluation').value=eid;renderMetrics();renderMonitoring();renderEvaluation();",context);
 return {c:context,nodes,run:s=>vm.runInContext(s,context),text:id=>nodes[id]?.textContent||''};
}
async function main(){
 let h=harness(frames.a35);assert.match(h.text('journey-context'),/mission-crew-A-cycle-35/);assert.match(h.text('journey-links'),/3. Prevención documentada/);assert.match(h.text('astronaut-guidance'),/Baseline utilizado: mission-crew-A-baseline/);assert.match(h.text('astronaut-guidance'),/Cambio:/);assert.match(h.text('astronaut-guidance'),/no diagnóstico ni causalidad/);assert.match(h.text('astronaut-guidance'),/Recursos|recursos/);passed++;
 assert.match(h.text('astronaut-guidance'),/Densidad mineral ósea/);assert.match(h.text('astronaut-guidance'),/Carga viral/);assert.match(h.text('astronaut-guidance'),/Tiempo de reacción/);assert.match(h.text('astronaut-guidance'),/No medido/);passed++;
 h=harness(frames.a21);assert.match(h.text('astronaut-guidance'),/Datos contradictorios/);assert.match(h.text('astronaut-guidance'),/no se considera normal/);assert.match(h.text('astronaut-guidance'),/Fase de medición incompatible/);h.run("$('variable').value='physiology.strength';renderChart()");assert.match(h.text('chart'),/Sin datos válidos/);passed++;
 h=harness(frames.b18,frames.b18.monitoring.at(-1).clinical_evaluations.DKA.id);assert.match(h.text('persistent-clinical-alert'),/Emergencia/);assert.match(h.text('protocol-list'),/POTASSIUM/);assert.match(h.text('protocol-list'),/AUTHORIZATION_REQUIRED/);assert.match(h.text('journey-evaluation'),/Pertenece explícitamente/);h.run("showView('followup')");assert.equal(h.nodes['persistent-clinical-alert'].hidden,false);passed++;
 h=harness(frames.b47,frames.b18.monitoring.at(-1).clinical_evaluations.DKA.id);assert.match(h.text('journey-evaluation'),/Contexto distinto/);assert.match(h.text('journey-evaluation'),/Ir al ciclo de origen/);passed++;
 h.c.target=frames.b18;h.c.dest=frames.b18.monitoring.at(-1).clinical_evaluations.DKA.id;h.run("loadSubject=async function(){dashboard=target;};");await h.run("openCycleEvaluation(dest,'mission-crew-B-cycle-18')");assert.equal(h.run('selected.id'),h.c.dest);assert.equal(h.run('currentView'),'clinical');assert.equal(h.nodes['mission-frame'].value,'frame-mission-crew-B-cycle-18');passed++;
 h=harness(frames.a35);h.c.bad=frames.b18.monitoring.at(-1).clinical_evaluations.DKA.id;await h.run("openCycleEvaluation(bad,'mission-crew-B-cycle-18')");assert.match(h.text('error'),/No hay vínculo explícito/);assert.equal(h.nodes['mission-frame'].value,frames.a35.historical_frame.id);passed++;
 h=harness(frames.b47,frames.b18.monitoring.at(-1).clinical_evaluations.DKA.id);h.c.dest=frames.b18.monitoring.at(-1).clinical_evaluations.DKA.id;h.c.other=frames.a35;h.run("loadSubject=async function(){dashboard=other;};");await h.run("openCycleEvaluation(dest,'mission-crew-B-cycle-18')");assert.equal(h.run('selected'),null);passed++;
 h=harness(frames.a35);h.run("$('variable').value='physiology.vo2max';renderChart()");assert.ok(h.nodes.chart.children[0].children.some(n=>n.attrs.class==='baseline'));h.run("currentCycle().domains.flatMap(d=>d.indicators).find(i=>i.variable==='physiology.vo2max').baseline_comparison=null;renderChart()");assert.ok(!h.nodes.chart.children[0].children.some(n=>n.attrs.class==='baseline'));passed++;
 h=harness(frames.a35);h.run("$('variable').value='physiology.vo2max';const allowed=dashboard.measurements.filter(r=>r.measurement.variable==='physiology.vo2max'&&chartAllows(r));allowed[0].measurement.unit='heterogeneous-test-unit';renderChart()");assert.match(h.text('chart'),/Unidades heterogéneas/);passed++;
 h=harness(frames.a35);h.run("$('subject').value=JSON.stringify(['missing-subject','missing-mission']);api=async()=>{throw Error('Controlled offline failure')};");await h.run('loadSubject()');assert.equal(h.text('journey-links'),'');assert.match(h.text('journey-context'),/Cargando contexto/);assert.match(h.text('error'),/Controlled offline failure/);passed++;
 h=harness(frames.a35);h.run("const marker='<img src=x onerror=attack>';dashboard.monitoring.at(-1).domains[0].indicators[0].quality_issues.push({reason:marker});renderAstronautGuidance()");assert.match(h.text('astronaut-guidance'),/<img src=x/);assert.ok(!h.nodes['astronaut-guidance'].children.some(n=>n.tag==='img'));passed++;
 console.log(JSON.stringify({simulated_DOM_cases:passed,real_browser:false,network_requests:0}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});