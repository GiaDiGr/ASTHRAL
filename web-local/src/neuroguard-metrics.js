export const TLX_DIMENSIONS = [
  {id:'mental',label:'Mental demand',low:'Low',high:'High'},
  {id:'physical',label:'Physical demand',low:'Low',high:'High'},
  {id:'temporal',label:'Temporal demand',low:'Low',high:'High'},
  {id:'performance',label:'Own performance',low:'Good',high:'Poor'},
  {id:'effort',label:'Effort',low:'Low',high:'High'},
  {id:'frustration',label:'Frustration',low:'Low',high:'High'}
];

export const TLX_PAIRS = TLX_DIMENSIONS.flatMap((left,index)=>
  TLX_DIMENSIONS.slice(index+1).map(right=>({factor_a:left.id,factor_b:right.id}))
);

export const KSS_ANCHORS = [
  'Extremely alert','Very alert','Alert','Rather alert','Neither alert nor sleepy',
  'Some signs of sleepiness','Sleepy, no effort to keep awake',
  'Sleepy, some effort to keep awake','Very sleepy, great effort, fighting sleep'
];

export function weightedTlx(ratings,choices) {
  if(!ratings||!Array.isArray(choices)||choices.length!==15) throw Error('Complete six NASA-TLX ratings and all 15 pairwise choices.');
  const ids=TLX_DIMENSIONS.map(({id})=>id);
  if(Object.keys(ratings).sort().join('|')!==[...ids].sort().join('|')) throw Error('NASA-TLX ratings must include exactly the six named dimensions.');
  const weights=Object.fromEntries(TLX_DIMENSIONS.map(({id})=>[id,0]));
  const seen=new Set();
  for(const choice of choices) {
    const {factor_a,factor_b,selected}=choice||{};
    if(!ids.includes(factor_a)||!ids.includes(factor_b)||factor_a===factor_b||!ids.includes(selected)||![factor_a,factor_b].includes(selected)) throw Error('Invalid NASA-TLX pair selection.');
    const pair=[factor_a,factor_b].sort().join('|');
    if(seen.has(pair)) throw Error('Each NASA-TLX pair must appear exactly once.');
    seen.add(pair);
    weights[selected]++;
  }
  if(seen.size!==15||Object.values(ratings).some(v=>!Number.isInteger(v)||v<0||v>100||v%5)) throw Error('NASA-TLX ratings must use 0–100 in increments of 5 and all 15 pairs.');
  return {
    weights,
    weighted_score:Math.round(TLX_DIMENSIONS.reduce((sum,{id})=>sum+ratings[id]*weights[id],0)/15*100)/100,
    unweighted_descriptive_mean:Math.round(TLX_DIMENSIONS.reduce((sum,{id})=>sum+ratings[id],0)/6*100)/100
  };
}

export function summarizeReactionTrials(trials) {
  const valid=trials.filter(({response_ms})=>Number.isFinite(response_ms)&&response_ms>=100).map(({response_ms})=>response_ms);
  const sorted=[...valid].sort((a,b)=>a-b),mean=valid.length?valid.reduce((a,b)=>a+b,0)/valid.length:null;
  const median=sorted.length?sorted.length%2?sorted[(sorted.length-1)/2]:(sorted[sorted.length/2-1]+sorted[sorted.length/2])/2:null;
  return {
    count:trials.length,
    median_rt_ms:median,
    sd_rt_ms:mean===null?null:Math.round(Math.sqrt(valid.reduce((sum,x)=>sum+(x-mean)**2,0)/valid.length)*100)/100,
    lapses_355ms:valid.filter(x=>x>=355).length+trials.filter(x=>x.timed_out).length,
    lapses_500ms:valid.filter(x=>x>=500).length+trials.filter(x=>x.timed_out).length,
    anticipations:trials.filter(x=>Number.isFinite(x.response_ms)&&x.response_ms<100).length,
    timeouts:trials.filter(x=>x.timed_out).length
  };
}

export function csvCell(value) {
  let text=value==null?'':typeof value==='object'?JSON.stringify(value):String(value);
  if(/^[\s]*[=+@-]/.test(text)) text="'"+text;
  return '"'+text.replaceAll('"','""')+'"';
}

export function neuroguardEntries(entries) {
  return Array.isArray(entries)?entries.filter(row=>row?.entry_type==='WELLBEING'&&row.neuroguard&&typeof row.neuroguard==='object'):[];
}
