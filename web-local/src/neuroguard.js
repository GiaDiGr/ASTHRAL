import {downloadLocalJson} from './longitudinal-views.js';
import {KSS_ANCHORS,TLX_DIMENSIONS,TLX_PAIRS,csvCell,neuroguardEntries,weightedTlx} from './neuroguard-metrics.js';

const $=id=>document.getElementById(id);
const el=(tag,text='')=>{const element=document.createElement(tag);element.textContent=text;return element;};
const nowIso=()=>new Date().toISOString();
const CONSENT_VERSION='ASTHRAL_NEUROGUARD_CONSENT_1';

function page(workspace) {
  if($('#neuroguard')) return $('#neuroguard');
  const root=el('section');root.id='neuroguard';root.className='workspace-page mission-support-page';root.hidden=true;
  const intro=el('div');intro.className='page-intro';intro.append(el('p','VOLUNTARY PRIVATE TRACKING'),el('h1','NeuroGuard'),el('p','Experimental self-reports and short browser tasks for descriptive personal tracking. This module does not screen, diagnose, predict fitness for duty, or authorize a clinical or operational decision.'));
  root.append(intro);workspace.append(root);
  const nav=$('workspace-nav')?.querySelector('.more-nav>div');
  if(nav&&!nav.querySelector('[data-view="neuroguard"]')){const link=el('a','NeuroGuard');link.href='#neuroguard';link.dataset.view='neuroguard';nav.append(link);}
  return root;
}

function section(parent,title,description) {
  const block=el('section');block.className='ng-section';block.append(el('h2',title));
  if(description)block.append(el('p',description));parent.append(block);return block;
}

function labelControl(parent,label,type='text',options=[]) {
  const wrap=el('label',label);let input;
  if(type==='select'){
    input=document.createElement('select');
    const placeholder=el('option','Choose an option');placeholder.value='';input.append(placeholder);
    for(const [value,text] of options){const option=el('option',text);option.value=value;input.append(option);}
  } else {input=document.createElement('input');input.type=type;}
  input.setAttribute('aria-label',label);wrap.append(input);parent.append(wrap);return input;
}

function slider(parent,label,{min=0,max=10,step=1,value=5,low='Low',high='High'}={}) {
  const wrap=el('label');wrap.className='ng-slider';
  const title=el('span',`${label} · ${value}/${max}`);wrap.append(title);
  const input=document.createElement('input');input.type='range';input.min=String(min);input.max=String(max);input.step=String(step);input.value=String(value);input.setAttribute('aria-label',label);
  input.addEventListener('input',()=>title.textContent=`${label} · ${input.value}/${max}`);
  const anchors=el('small',`${low} · ${high}`);wrap.append(input,anchors);parent.append(wrap);return input;
}

function action(parent,text,onClick,kind='button') {
  const control=el('button',text);control.type='button';if(kind==='primary')control.className='primary-action';
  control.addEventListener('click',async()=>{control.disabled=true;try{await onClick();}catch(error){const status=parent.querySelector('[role="status"]');if(status)status.textContent=error.message;else throw error;}finally{control.disabled=false;}});
  parent.append(control);return control;
}

function status(parent) {const result=el('p');result.className='ng-status';result.setAttribute('role','status');result.setAttribute('aria-live','polite');parent.append(result);return result;}

function metric(title,value,source) {
  const card=el('article');card.append(el('h3',title),el('p',value??'Not recorded'),el('small',source));return card;
}

function localSeries(parent,title,rows,readout,unit) {
  const block=el('section');block.className='ng-trend';block.append(el('h3',title),el('p','Descriptive recorded values only. No target, threshold or risk color is applied.'));
  const points=rows.map(row=>({date:row.occurred_at,value:readout(row)})).filter(point=>Number.isFinite(point.value)).slice(-20);
  if(!points.length){block.append(el('p','No observations in this interval.'));parent.append(block);return;}
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 720 220');svg.setAttribute('role','img');svg.setAttribute('aria-label',title);
  const values=points.map(point=>point.value),min=Math.min(...values),max=Math.max(...values),span=Math.max(1,max-min),step=660/Math.max(1,points.length);
  points.forEach((point,index)=>{
    const y=185-145*(point.value-min)/span,x=32+index*step;
    const bar=document.createElementNS(svg.namespaceURI,'rect');bar.setAttribute('x',String(x));bar.setAttribute('y',String(y));bar.setAttribute('width',String(Math.max(5,step-5)));bar.setAttribute('height',String(Math.max(2,185-y)));bar.setAttribute('rx','3');bar.setAttribute('fill','#147c78');
    const titleNode=document.createElementNS(svg.namespaceURI,'title');titleNode.textContent=`${new Date(point.date).toLocaleString()}: ${point.value} ${unit}`;bar.append(titleNode);svg.append(bar);
    const label=document.createElementNS(svg.namespaceURI,'text');label.setAttribute('x',String(x));label.setAttribute('y','204');label.setAttribute('font-size','9');label.textContent=new Date(point.date).toLocaleDateString();svg.append(label);
  });
  block.append(svg);parent.append(block);
}

export function installNeuroGuard({workspace,call,persist,isTemporary=()=>false,getEntries=()=>[]}={}) {
  if(!workspace)throw Error('NeuroGuard workspace is unavailable.');
  const root=page(workspace),dashboard=section(root,'NeuroGuard dashboard','Each panel shows a separate source and metric. No combined mental-health or mission-risk score is computed.');
  const range=labelControl(dashboard,'Trend interval','select',[['7','Last 7 days'],['30','Last 30 days'],['90','Last 90 days'],['all','All recorded']]);range.value='30';
  const summary=document.createElement('div');summary.className='metric-grid';dashboard.append(summary);
  const charts=document.createElement('div');charts.className='ng-chart-grid';dashboard.append(charts);

  const consent=section(root,'Voluntary participation','Use is optional. Results are saved only in the currently unlocked ASTHRAL profile. Temporary synthetic demo records stay in memory and are discarded when you leave the demo. No camera, microphone or external service is used by these self-reports and tasks.');
  const consentLabel=el('label');consentLabel.className='check-option';
  const consentBox=document.createElement('input');consentBox.type='checkbox';consentBox.setAttribute('aria-label','I consent to voluntarily record selected NeuroGuard sessions locally');
  consentLabel.append(consentBox,el('span','I freely choose to record the NeuroGuard sessions I submit in this local profile. I can decline, stop, or delete a saved NeuroGuard session.'));consent.append(consentLabel);
  let consentedAt=null;consentBox.addEventListener('change',()=>{consentedAt=consentBox.checked?nowIso():null;});
  function consentFields(){if(!consentBox.checked||!consentedAt)throw Error('Check the voluntary participation box before saving a session.');return {consent_given:true,consent_version:CONSENT_VERSION,consented_at:consentedAt};}
  const consentStatus=status(consent);

  const mood=section(root,'1 · Mood Check','Four experimental 0–10 self-ratings. These are not a validated questionnaire, screening result or diagnosis. Higher values mean more of the named quality; the tension scale is intentionally not reversed.');
  const moodControls={
    mood:slider(mood,'Perceived mood',{low:'Very low',high:'Very positive'}),
    energy:slider(mood,'Subjective energy',{low:'Very low',high:'Very high'}),
    tension:slider(mood,'Perceived tension',{low:'None',high:'Very high'}),
    wellbeing:slider(mood,'Overall subjective well-being',{low:'Very low',high:'Very high'})
  };
  const moodNote=labelControl(mood,'Optional private observation','text');moodNote.maxLength=1000;
  const moodStatus=status(mood);
  action(mood,'Save Mood Check',async()=>{
    const saved=await save('MOOD_CHECK',{mood_0_10:Number(moodControls.mood.value),energy_0_10:Number(moodControls.energy.value),tension_0_10:Number(moodControls.tension.value),wellbeing_0_10:Number(moodControls.wellbeing.value)},moodNote.value);
    moodStatus.textContent=`Saved voluntary mood self-report at ${new Date(saved.occurred_at).toLocaleString()}. No screening or diagnosis.`;
  },'primary');

  const fatigue=section(root,'2 · Fatigue Monitor','KSS wording uses the nine-point scale and asks about the previous five minutes. Mental and physical fatigue sliders below are ASTHRAL experimental self-ratings, not validated scales. Sleep remains a separate user-entered record.');
  const kss=labelControl(fatigue,'Karolinska Sleepiness Scale · level over the past 5 minutes','select',KSS_ANCHORS.map((text,index)=>[String(index+1),`${index+1} · ${text}`]));
  const kssStatus=status(fatigue);
  action(fatigue,'Save KSS',async()=>{
    if(!kss.value)throw Error('Select one of the nine KSS levels.');
    const saved=await save('KSS',{score:Number(kss.value)},'');kssStatus.textContent=`Saved KSS ${saved.neuroguard.score}/9 · ${saved.neuroguard.anchor.replaceAll('_',' ').toLowerCase()} · the rating is self-reported, not a fitness determination.`;
  });
  const fatigueControls={mental:slider(fatigue,'Mental fatigue',{low:'None',high:'Very high'}),physical:slider(fatigue,'Physical fatigue',{low:'None',high:'Very high'})};
  const sleepSelect=labelControl(fatigue,'Optional link to a previously logged sleep interval','select',[]);
  const sleepSummary=el('p','No sleep interval linked. Add sleep details in Sleep & Recovery if desired.');fatigue.append(sleepSummary);
  const sleepLink=el('a','Open Sleep & Recovery');sleepLink.href='#sleep-recovery';sleepLink.dataset.view='sleep-recovery';fatigue.append(sleepLink);
  const fatigueStatus=status(fatigue);
  action(fatigue,'Save fatigue self-ratings',async()=>{
    const sleepId=sleepSelect.value||undefined;
    const saved=await save('FATIGUE_CHECK',{mental_fatigue_0_10:Number(fatigueControls.mental.value),physical_fatigue_0_10:Number(fatigueControls.physical.value),...(sleepId?{linked_sleep_entry_id:sleepId}:{})},'');
    fatigueStatus.textContent=`Saved mental and physical fatigue self-ratings. ${saved.neuroguard.linked_sleep_summary?'A selected local sleep entry is linked.':'No sleep entry was linked.'}`;
  },'primary');

  const stressWork=section(root,'3 · Stress & Workload','Current perceived stress is a separate experimental self-rating. NASA-TLX rates six task-load dimensions; its weighted score and an unweighted descriptive mean are shown separately. Neither is a clinical measure of anxiety or stress disorder.');
  const stressContext=labelControl(stressWork,'Perceived-stress context','select',[['GENERAL','General'],['BEFORE_ACTIVITY','Before an activity'],['AFTER_ACTIVITY','After an activity']]);
  const stressSlider=slider(stressWork,'Current perceived stress',{low:'None',high:'Very high'});
  const stressStatus=status(stressWork);
  action(stressWork,'Save perceived stress',async()=>{
    const saved=await save('STRESS_CHECK',{stress_0_10:Number(stressSlider.value),task_context:stressContext.value||'GENERAL'},'');
    stressStatus.textContent=`Saved perceived stress ${saved.neuroguard.stress_0_10}/10 · ${saved.neuroguard.task_context}. Not a clinical stress assessment.`;
  });
  stressWork.append(el('h3','NASA Task Load Index (NASA-TLX)'));
  stressWork.append(el('p','First rate the magnitude of each dimension from 0–100 in 5-point increments. “Own performance” runs from good to poor. Then make one pairwise choice for each of the 15 pairs, selecting the dimension that contributed more to the workload of the named task. The original weighted score is Σ(rating × pairwise weight) / 15.'));
  const tlxTask=labelControl(stressWork,'Task or activity label','text');tlxTask.maxLength=120;
  const ratings={};
  for(const dimension of TLX_DIMENSIONS){
    const select=labelControl(stressWork,`${dimension.label} (${dimension.low} → ${dimension.high})`,'select',Array.from({length:21},(_,i)=>[String(i*5),String(i*5)]));ratings[dimension.id]=select;
  }
  const pairGroup=section(stressWork,'15 pairwise comparisons','Choose which of each pair contributed more to workload. Every pair is required once; weights are tallied by ASTHRAL and checked by the local engine.');
  const pairInputs=[];
  const pairOrder=[...TLX_PAIRS];
  for(let i=pairOrder.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[pairOrder[i],pairOrder[j]]=[pairOrder[j],pairOrder[i]];}
  for(const pair of pairOrder){
    const a=TLX_DIMENSIONS.find(x=>x.id===pair.factor_a),b=TLX_DIMENSIONS.find(x=>x.id===pair.factor_b);
    const input=labelControl(pairGroup,`${a.label} or ${b.label}`,'select',[[pair.factor_a,a.label],[pair.factor_b,b.label]]);pairInputs.push({...pair,input});
  }
  const tlxContext=labelControl(stressWork,'NASA-TLX rating context','select',[['GENERAL','General task'],['BEFORE_ACTIVITY','Before activity'],['AFTER_ACTIVITY','After activity']]);
  const tlxStatus=status(stressWork);
  action(stressWork,'Save weighted NASA-TLX',async()=>{
    if(Object.values(ratings).some(input=>input.value==='')||pairInputs.some(pair=>pair.input.value===''))throw Error('Complete all six ratings and all 15 pairwise choices.');
    const cleanRatings=Object.fromEntries(Object.entries(ratings).map(([key,input])=>[key,Number(input.value)]));
    const choices=pairInputs.map(pair=>({factor_a:pair.factor_a,factor_b:pair.factor_b,selected:pair.input.value}));
    weightedTlx(cleanRatings,choices);
    const saved=await save('NASA_TLX_WEIGHTED',{ratings:cleanRatings,pairwise_choices:choices,task_context:[tlxContext.value||'GENERAL',tlxTask.value.trim()].filter(Boolean).join(' · ')},'');
    tlxStatus.textContent=`Saved weighted NASA-TLX: ${saved.neuroguard.weighted_score}/100 · unweighted descriptive mean ${saved.neuroguard.unweighted_descriptive_mean}/100. Scores are task-load descriptions, not mental-health findings.`;
  },'primary');

  const visual=section(root,'4 · Visual Fatigue','Camera analysis is unavailable in this build. NeuroGuard does not request webcam access or retain images, video or audio. MediaPipe Holistic is pinned in the separate MotionGuard pipeline, but no locally validated face/eyelid quality-control pipeline or calibrated PERCLOS method is integrated here.');
  const cameraState=el('p','Status: disabled · no automatic emotion, fatigue, sleepiness, blink-duration or physiological inference.');cameraState.className='notice';visual.append(cameraState);

  const cognition=section(root,'5 · Cognitive Performance','These browser tasks are exploratory research software. Browser event timing, display refresh, touch latency, interruptions, device and practice effects are not calibrated. Results are not norms, diagnosis, fitness-for-duty findings or NASA RST scores. You may stop a task at any time; interrupted trials are discarded.');
  const pvtIntro=el('p','PVT-B paradigm-inspired task: 3-minute stimulus window; random 1–4 second response-to-next-stimulus interval including 1 second of response feedback; responses under 100 ms are false starts; responses at or above 355 ms and 500 ms are counted separately as lapses; no response after 30 seconds is a timeout lapse. A final open trial can extend elapsed time by up to 30 seconds. This is not the NASA Reaction Self Test: its timing, device and algorithms are not equivalent or validated.');cognition.append(pvtIntro);
  const taskStage=el('div');taskStage.className='ng-task-stage';
  const taskStatus=status(taskStage),stimulus=el('div','Ready');stimulus.className='ng-stimulus';stimulus.setAttribute('aria-live','polite');
  const responseButton=el('button','Respond · Space');responseButton.type='button';responseButton.className='ng-response';responseButton.disabled=true;
  const taskActions=el('div');taskActions.className='row';taskStage.append(stimulus,responseButton,taskActions);cognition.append(taskStage);
  const pvtStart=action(taskActions,'Start 3-minute PVT-B browser task',()=>startReaction('PVT_B_BROWSER_RESEARCH',180000),'primary');
  const simpleStart=action(taskActions,'Start simple reaction-time task (10 trials)',()=>startReaction('SIMPLE_RT_BROWSER_RESEARCH',null),'button');
  const stopTask=action(taskActions,'Stop and discard active task',()=>{if(activeTask){hideAbort();taskStatus.textContent='Task stopped by you; incomplete measurements were discarded.';}},'button');stopTask.disabled=true;
  const memoryStart=action(cognition,'Start 1-back working-memory task (research practice)',()=>startMemoryTask(),'button');
  const goStart=action(cognition,'Start Go/No-Go inhibitory-control task (20 trials)',()=>startGoNoGo(),'button');
  const memoryControls=section(cognition,'1-back response controls','Tap SAME or DIFFERENT for each symbol compared with the immediately previous one. No population norms are used.');
  const memorySame=el('button','Same');memorySame.type='button';memorySame.disabled=true;
  const memoryDifferent=el('button','Different');memoryDifferent.type='button';memoryDifferent.disabled=true;
  memoryControls.append(memorySame,memoryDifferent);
  const cognitiveHistory=section(root,'Cognitive-session history','Individual tasks and their raw user responses stay separate. First recorded sessions are only descriptive anchors; repeated-test changes may reflect practice, device and conditions.');
  const sessionRows=el('div');sessionRows.className='ng-history metric-grid';cognitiveHistory.append(sessionRows);

  let activeTask=null,stimulusTimer=null,timeoutTimer=null,counterTimer=null,hiddenListener=null;
  function currentRows(){return getEntries()||[];}
  function getConsent(){return consentFields();}
  async function save(task,payload,note=''){
    const consentData=getConsent();
    const neuroguard={task,...payload,...consentData};
    const row=await call('prevention_add',{entry_type:'WELLBEING',occurred_at:nowIso(),label:`NeuroGuard ${task.replaceAll('_',' ').toLowerCase()}`,note,neuroguard,synthetic_fixture:isTemporary()});
    await persist();currentRows().push(row);render();return row;
  }
  function setTaskBusy(busy){for(const control of [pvtStart,simpleStart,memoryStart,goStart])control.disabled=busy;responseButton.disabled=!busy;stopTask.disabled=!busy;}
  function clearTimers(){clearTimeout(stimulusTimer);clearTimeout(timeoutTimer);clearInterval(counterTimer);stimulusTimer=timeoutTimer=counterTimer=null;}
  function hideAbort(){
    if(!activeTask)return;
    const previous=activeTask,name=previous.task;clearTimers();clearTimeout(previous.advanceTimer);clearTimeout(previous.trialTimer);
    if(previous.same)previous.same.disabled=true;if(previous.different)previous.different.disabled=true;
    activeTask=null;setTaskBusy(false);responseButton.disabled=true;stimulus.textContent='Ready';
    taskStatus.textContent=`${name.replaceAll('_',' ')} interrupted when the tab became hidden. Incomplete measurements were discarded.`;
    if(hiddenListener)document.removeEventListener('visibilitychange',hiddenListener);hiddenListener=null;
  }
  function guardVisibility(){hiddenListener=()=>{if(document.hidden)hideAbort();};document.addEventListener('visibilitychange',hiddenListener);}
  function finishTaskCleanup(){const previous=activeTask;clearTimers();clearTimeout(previous?.advanceTimer);clearTimeout(previous?.trialTimer);if(hiddenListener)document.removeEventListener('visibilitychange',hiddenListener);hiddenListener=null;if(previous?.same)previous.same.disabled=true;if(previous?.different)previous.different.disabled=true;activeTask=null;setTaskBusy(false);responseButton.disabled=true;stimulus.textContent='Ready';}
  function drawReaction(){
    const run=activeTask;if(!run)return;
    const elapsed=performance.now()-run.started;
    if(!run.duration&&run.trials.length>=10){finishReaction();return;}
    if(run.duration&&elapsed>=run.duration&&!run.current){finishReaction();return;}
    const delay=run.nextInterval;
    taskStatus.textContent=run.task==='PVT_B_BROWSER_RESEARCH'?`3-minute stimulus window · ${Math.min(180,Math.floor(elapsed/1000))}/180 seconds · ${run.trials.length} trials`:`Simple reaction-time task · ${run.trials.length}/10 trials`;
    stimulusTimer=setTimeout(()=>{
      if(activeTask!==run)return;
      const now=performance.now(),since=now-run.started;
      if(run.duration&&since>=run.duration){if(run.current)return;finishReaction();return;}
      const trial={stimulus_onset_ms:Math.round(since),interval_ms:delay,stimulusAt:now,response_ms:null,timed_out:false};run.current=trial;
      stimulus.textContent='0000';stimulus.classList.add('ng-stimulus-active');responseButton.disabled=false;
      counterTimer=setInterval(()=>{if(activeTask===run&&run.current)stimulus.textContent=String(Math.min(30000,Math.round(performance.now()-run.current.stimulusAt))).padStart(4,'0');},32);
      timeoutTimer=setTimeout(()=>{
        if(activeTask!==run||!run.current)return;
        trial.timed_out=true;trial.response_ms=null;run.trials.push({...trial});run.current=null;clearInterval(counterTimer);counterTimer=null;responseButton.disabled=true;
        stimulus.classList.remove('ng-stimulus-active');stimulus.textContent='No response · 30,000 ms timeout';
        nextReaction(run,1000+Math.floor(Math.random()*3001));
      },30000);
    },delay);
  }
  function nextReaction(run,interval){
    if(activeTask!==run)return;
    const elapsed=performance.now()-run.started;
    if(run.duration&&elapsed>=run.duration){if(!run.current)finishReaction();return;}
    run.nextInterval=interval;responseButton.disabled=false;drawReaction();
  }
  function respondReaction(){
    const run=activeTask;if(!run)return;
    const now=performance.now();
    if(!run.current){run.falseStarts.push({elapsed_ms:Math.round(now-run.started),reason:'NO_STIMULUS'});stimulus.textContent='False start · wait for the signal';return;}
    const current=run.current,rt=Math.round(now-current.stimulusAt);clearTimeout(timeoutTimer);clearInterval(counterTimer);timeoutTimer=counterTimer=null;
    current.response_ms=rt;current.timed_out=false;run.trials.push({...current});run.current=null;responseButton.disabled=true;
    stimulus.classList.remove('ng-stimulus-active');stimulus.textContent=rt<100?`False start · ${rt} ms`:`${rt} ms`;
    nextReaction(run,1000+Math.floor(Math.random()*3001));
  }
  function startReaction(task,duration){
    getConsent();if(activeTask)throw Error('Finish or stop the active cognitive task first.');
    activeTask={task,duration,started:performance.now(),trials:[],falseStarts:[],current:null,nextInterval:duration?1000+Math.floor(Math.random()*3001):1500+Math.floor(Math.random()*2501)};
    setTaskBusy(true);guardVisibility();stimulus.classList.remove('ng-stimulus-active');stimulus.textContent='Wait for the signal';
    taskStatus.textContent=duration?'Beginning 3-minute task…':'Beginning 10-trial simple reaction-time task…';drawReaction();
  }
  async function finishReaction(){
    const run=activeTask;if(!run)return;
    const elapsed=Math.max(run.duration||0,Math.ceil(performance.now()-run.started));
    const trials=run.trials.map(({stimulus_onset_ms,interval_ms,response_ms,timed_out})=>({stimulus_onset_ms,interval_ms,response_ms,timed_out}));
    const payload={trials,total_elapsed_ms:elapsed,false_start_events:run.falseStarts};
    finishTaskCleanup();
    try{
      const row=await save(run.task,payload,'Browser task; exploratory software record; device timing is not calibrated.');
      taskStatus.textContent=`Saved ${row.neuroguard.task.replaceAll('_',' ')} · ${row.neuroguard.trials.length} trials · median response ${row.neuroguard.median_rt_ms??'not available'} ms · timing is not clinically validated.`;
    }catch(error){taskStatus.textContent=`Task finished but the result could not be saved: ${error.message}`;}
  }
  async function runMemory(){
    const run=activeTask;if(!run)return;
    if(run.index>=run.sequence.length){const {sequence,trials}=run;finishTaskCleanup();try{const row=await save('WORKING_MEMORY_1BACK_BROWSER_RESEARCH',{sequence,trials},'Unvalidated one-back practice task; browser timing and practice effects apply.');taskStatus.textContent=`Saved 1-back task · ${row.neuroguard.correct_responses}/19 correct · accuracy ${(row.neuroguard.accuracy_fraction*100).toFixed(1)}% · descriptive only.`;}catch(error){taskStatus.textContent='Task finished but saving failed: '+error.message;}return;}
    const index=run.index,stim=run.sequence[index],previous=run.sequence[index-1],onset=performance.now()-run.started;
    const trial={index,stimulus:stim,previous_stimulus:previous,stimulus_onset_ms:Math.round(onset),response:null,response_ms:null};
    run.current=trial;stimulus.classList.remove('ng-stimulus-active');stimulus.textContent=stim;taskStatus.textContent=`1-back research task · ${index}/19 scored trials · Is this the same as the previous symbol?`;
    run.responseWindowStart=performance.now();
    run.same.disabled=run.different.disabled=false;
    run.advanceTimer=setTimeout(()=>recordMemoryAnswer(null),1800);
  }
  function recordMemoryAnswer(answer){
    const run=activeTask;if(!run||!run.current||run.current.response!==null)return;
    clearTimeout(run.advanceTimer);const trial=run.current;
    if(answer!==null){trial.response=answer;trial.response_ms=Math.round(performance.now()-run.responseWindowStart);}
    else {trial.response=null;trial.response_ms=null;}
    run.trials.push({...trial});run.current=null;run.same.disabled=run.different.disabled=true;run.index++;
    stimulus.textContent=answer===null?'No response recorded':'Response recorded';run.advanceTimer=setTimeout(()=>runMemory(),300);
  }
  memorySame.addEventListener('click',()=>recordMemoryAnswer('SAME'));
  memoryDifferent.addEventListener('click',()=>recordMemoryAnswer('DIFFERENT'));
  async function startMemoryTask(){
    getConsent();if(activeTask)throw Error('Finish or stop the active cognitive task first.');
    const sequence=[['A','B','C','D'][Math.floor(Math.random()*4)]];
    // Generate exactly five SAME trials; all other transitions differ.
    const targetIndices=new Set();while(targetIndices.size<5){const candidate=1+Math.floor(Math.random()*19);if(!targetIndices.has(candidate)&&![...targetIndices].some(index=>Math.abs(index-candidate)===1))targetIndices.add(candidate);}
    for(let index=1;index<20;index++){const candidates=targetIndices.has(index)?[sequence[index-1]]:['A','B','C','D'].filter(value=>value!==sequence[index-1]);sequence.push(candidates[Math.floor(Math.random()*candidates.length)]);}
    activeTask={task:'WORKING_MEMORY_1BACK_BROWSER_RESEARCH',started:performance.now(),sequence,trials:[],index:1,current:null,same:memorySame,different:memoryDifferent,advanceTimer:null};responseButton.disabled=true;
    setTaskBusy(true);guardVisibility();runMemory();
  }
  async function runGoNoGo(){
    const run=activeTask;if(!run)return;
    if(run.index>=run.plan.length){const trials=run.trials;finishTaskCleanup();try{const row=await save('INHIBITORY_GONOGO_BROWSER_RESEARCH',{trials},'Unvalidated go/no-go practice task; not an operational or diagnostic measure.');taskStatus.textContent=`Saved Go/No-Go task · ${row.neuroguard.false_alarms} false alarms · ${row.neuroguard.go_omissions} go omissions · descriptive only.`;}catch(error){taskStatus.textContent='Task finished but saving failed: '+error.message;}return;}
    const index=run.index,noGo=run.plan[index],onset=performance.now()-run.started;
    run.current={stimulus_onset_ms:Math.round(onset),stimulusAt:performance.now(),no_go:noGo,responded:false,response_ms:null};
    stimulus.textContent=noGo?'■ HOLD':'● RESPOND';stimulus.classList.toggle('ng-no-go',noGo);stimulus.classList.toggle('ng-go',!noGo);
    taskStatus.textContent=`Go/No-Go · ${index+1}/20 · ${noGo?'No-Go: withhold response':'Go: respond once'}`;responseButton.disabled=false;
    run.trialTimer=setTimeout(()=>{
      if(activeTask!==run||!run.current)return;
      run.trials.push({...run.current});run.current=null;responseButton.disabled=true;run.index++;
      run.advanceTimer=setTimeout(()=>runGoNoGo(),250);
    },900);
  }
  async function startGoNoGo(){
    getConsent();if(activeTask)throw Error('Finish or stop the active cognitive task first.');
    const plan=Array.from({length:20},(_,index)=>index<5);
    for(let i=plan.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[plan[i],plan[j]]=[plan[j],plan[i]];}
    activeTask={task:'INHIBITORY_GONOGO_BROWSER_RESEARCH',started:performance.now(),plan,trials:[],index:0,current:null,trialTimer:null,advanceTimer:null};
    setTaskBusy(true);guardVisibility();responseButton.disabled=true;runGoNoGo();
  }
  function recordGoNoGo(){
    const run=activeTask;if(!run||run.task!=='INHIBITORY_GONOGO_BROWSER_RESEARCH'||!run.current||run.current.responded)return;
    run.current.responded=true;run.current.response_ms=Math.max(0,Math.round(performance.now()-run.current.stimulusAt));
    stimulus.textContent=run.current.no_go?'False alarm recorded':'Response recorded';
  }
  // Space bar and the on-screen button route to the active task, never across task types.
  responseButton.addEventListener('click',()=>{if(activeTask?.task==='WORKING_MEMORY_1BACK_BROWSER_RESEARCH')return;if(activeTask?.task==='INHIBITORY_GONOGO_BROWSER_RESEARCH')recordGoNoGo();else respondReaction();});
  document.addEventListener('keydown',event=>{if(event.code!=='Space'||!activeTask)return;event.preventDefault();if(activeTask.task==='WORKING_MEMORY_1BACK_BROWSER_RESEARCH')return;if(activeTask.task==='INHIBITORY_GONOGO_BROWSER_RESEARCH')recordGoNoGo();else respondReaction();});

  function renderDashboard(rows){
    const selected=range.value,cutoff=selected==='all'?0:Date.now()-Number(selected)*86400000;
    const filtered=neuroguardEntries(rows).filter(row=>Date.parse(row.occurred_at)>=cutoff).sort((a,b)=>a.occurred_at.localeCompare(b.occurred_at));
    const latestTask=task=>filtered.filter(row=>row.neuroguard.task===task).at(-1);
    const last=filtered.at(-1);summary.replaceChildren();summary.append(metric('Latest NeuroGuard session',last?new Date(last.occurred_at).toLocaleString():'Not recorded','Voluntary self-report / browser task'));
    const m=latestTask('MOOD_CHECK')?.neuroguard;summary.append(metric('Mood / energy / tension / well-being',m?`${m.mood_0_10} / ${m.energy_0_10} / ${m.tension_0_10} / ${m.wellbeing_0_10} (0–10)`:'Not recorded','Experimental self-report'));
    const k=latestTask('KSS')?.neuroguard;summary.append(metric('KSS sleepiness',k?`${k.score}/9 · ${k.anchor.replaceAll('_',' ').toLowerCase()}`:'Not recorded','KSS self-report · previous five minutes'));
    const f=latestTask('FATIGUE_CHECK')?.neuroguard;summary.append(metric('Mental / physical fatigue',f?`${f.mental_fatigue_0_10} / ${f.physical_fatigue_0_10} (0–10)`:'Not recorded','Experimental self-report'));
    const s=latestTask('STRESS_CHECK')?.neuroguard;summary.append(metric('Perceived stress',s?`${s.stress_0_10}/10 · ${s.task_context}`:'Not recorded','Experimental self-report · separate from NASA-TLX'));
    const t=latestTask('NASA_TLX_WEIGHTED')?.neuroguard;summary.append(metric('NASA-TLX workload',t?`Weighted ${t.weighted_score}/100 · unweighted descriptive ${t.unweighted_descriptive_mean}/100`:'Not recorded','Task load · not a mental-health diagnosis'));
    const p=latestTask('PVT_B_BROWSER_RESEARCH')?.neuroguard;summary.append(metric('PVT-B paradigm browser task',p?`Median ${p.median_rt_ms??'—'} ms · lapses ≥355 ms: ${p.lapses_355ms} · false starts: ${p.anticipations}`:'Not recorded','Browser timing uncalibrated · not NASA RST'));
    charts.replaceChildren();
    localSeries(charts,'Mood self-rating · well-being / 10',filtered.filter(row=>row.neuroguard.task==='MOOD_CHECK'),row=>row.neuroguard.wellbeing_0_10,'/10');
    localSeries(charts,'Perceived stress self-rating',filtered.filter(row=>row.neuroguard.task==='STRESS_CHECK'),row=>row.neuroguard.stress_0_10,'/10');
    localSeries(charts,'KSS sleepiness',filtered.filter(row=>row.neuroguard.task==='KSS'),row=>row.neuroguard.score,'/9');
    localSeries(charts,'PVT-B browser median response time',filtered.filter(row=>row.neuroguard.task==='PVT_B_BROWSER_RESEARCH'),row=>row.neuroguard.median_rt_ms,'ms');
    localSeries(charts,'NASA-TLX weighted workload',filtered.filter(row=>row.neuroguard.task==='NASA_TLX_WEIGHTED'),row=>row.neuroguard.weighted_score,'/100');
  }
  function renderHistory(rows){
    sessionRows.replaceChildren();
    const items=neuroguardEntries(rows).sort((a,b)=>b.occurred_at.localeCompare(a.occurred_at));
    if(!items.length){sessionRows.append(el('p','No NeuroGuard sessions recorded.'));return;}
    for(const row of items){
      const data=row.neuroguard,item=el('article');
      item.append(el('h3',data.task.replaceAll('_',' ')),el('p',`${new Date(row.occurred_at).toLocaleString()} · ${row.synthetic_data?'synthetic demo':'private profile'} · source: ${data.source}`));
      const detail=el('details');detail.append(el('summary','View separate recorded measures and provenance'));
      const table=document.createElement('dl');
      for(const [key,value] of Object.entries(data))if(!['consented_at','consent_given','consent_version','source','clinical_execution','clinical_interpretation','task','schema_version','pairwise_choices','trials','false_start_events'].includes(key)){table.append(el('dt',key.replaceAll('_',' ')),el('dd',typeof value==='object'?JSON.stringify(value):String(value??'—')));}
      detail.append(table);item.append(detail);
      if(row.note)item.append(el('p',row.note));
      const del=el('button','Delete this NeuroGuard session');del.type='button';del.addEventListener('click',async()=>{if(!confirm('Delete this NeuroGuard session from this local profile? The audit log will retain a deletion event, not the deleted measurement.'))return;del.disabled=true;try{await call('prevention_delete',{id:row.id});await persist();const current=currentRows();const index=current.findIndex(entry=>entry.id===row.id);if(index>=0)current.splice(index,1);render();consentStatus.textContent='NeuroGuard session deleted from this local profile and audit event recorded.';}catch(error){del.disabled=false;consentStatus.textContent='Could not delete session: '+error.message;}});item.append(del);sessionRows.append(item);
    }
  }
  function renderSleepLink(rows){
    const sleep=rows.filter(row=>row.entry_type==='SLEEP').sort((a,b)=>b.occurred_at.localeCompare(a.occurred_at));
    const requestedId=sleepSelect.value;
    sleepSelect.replaceChildren();const noLink=el('option','Do not link a sleep interval');noLink.value='';sleepSelect.append(noLink);
    for(const row of sleep){const option=el('option',`${row.occurred_at.slice(0,10)} · ${row.duration_minutes} min · ${row.subjective_quality_1_5??'quality not entered'}/5`);option.value=row.id;sleepSelect.append(option);}
    sleepSelect.value=sleep.some(row=>row.id===requestedId)?requestedId:'';
    const linked=sleep.find(row=>row.id===sleepSelect.value),latest=sleep[0];
    const selected=linked||latest;
    sleepSummary.textContent=selected?`${linked?'Selected sleep interval to link':'Latest available sleep interval · not linked'}: ${selected.duration_minutes} minutes · quality ${selected.subjective_quality_1_5??'not recorded'} / 5 · ${selected.occurred_at}. Context is self-reported only; missing sleep is not zero.`:'No sleep interval available. Add a self-reported interval in Sleep & Recovery if desired.';
  }
  sleepSelect.addEventListener('change',()=>renderSleepLink(currentRows()));
  function render(){const rows=currentRows();renderDashboard(rows);renderHistory(rows);renderSleepLink(rows);}
  range.addEventListener('change',render);
  action(root,'Export NeuroGuard JSON (plaintext file)',()=>{const rows=neuroguardEntries(currentRows());if(!rows.length)throw Error('There are no NeuroGuard sessions to export.');downloadLocalJson('asthral-neuroguard-export.json',{exported_at:nowIso(),warning:'Plaintext export of sensitive voluntary self-reports and browser task data. Store and share securely.',entries:rows});},'button');
  action(root,'Export NeuroGuard CSV (plaintext file)',()=>{const rows=neuroguardEntries(currentRows());if(!rows.length)throw Error('There are no NeuroGuard sessions to export.');const columns=['occurred_at','subject_id','task','task_context','mood_0_10','energy_0_10','tension_0_10','wellbeing_0_10','score','anchor','mental_fatigue_0_10','physical_fatigue_0_10','stress_0_10','weighted_score','unweighted_descriptive_mean','median_rt_ms','sd_rt_ms','lapses_355ms','lapses_500ms','anticipations','timeouts_30000ms','correct_responses','accuracy_fraction','false_alarms','go_omissions','synthetic_data'];const lines=[columns.map(csvCell).join(',')];for(const row of rows){const data=row.neuroguard;lines.push(columns.map(key=>csvCell(key==='occurred_at'?row.occurred_at:key==='subject_id'?row.subject_id:key==='task'?data.task:key==='synthetic_data'?row.synthetic_data:data[key])).join(','));}const url=URL.createObjectURL(new Blob([lines.join('\r\n')],{type:'text/csv;charset=utf-8'}));const link=el('a');link.href=url;link.download='asthral-neuroguard-export.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'button');
  function refresh(){render();}
  function clear(){hideAbort();consentBox.checked=false;consentedAt=null;range.value='30';render();}
  refresh();
  return {refresh,clear};
}
