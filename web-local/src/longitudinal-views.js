export function radiationSeries(records){
 const groups=new Map();
 for(const row of records){
  if(!Number.isFinite(row.value)||!Number.isFinite(Date.parse(row.timestamp)))continue;
  const key=JSON.stringify([row.quantity_kind,row.unit,row.mode,row.quality,row.instrument_id,row.mission_segment,row.location]);
  if(!groups.has(key))groups.set(key,{quantity:row.quantity_kind,unit:row.unit,mode:row.mode,quality:row.quality,instrument:row.instrument_id,segment:row.mission_segment,location:row.location,points:[]});
  groups.get(key).points.push(row);
 }
 return [...groups.values()].map(group=>({...group,points:group.points.sort((a,b)=>Date.parse(a.timestamp)-Date.parse(b.timestamp))}));
}
export function downloadLocalJson(filename,data){
 const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function renderRadiationSeries(target,records){
 target.replaceChildren();
 for(const group of radiationSeries(records)){
  const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent=`${group.quantity} · ${group.unit} · ${group.mode} · quality ${group.quality}`;section.append(heading);
  const detail=document.createElement('p');detail.textContent=`${group.instrument||'Instrument unknown'} · ${group.segment} · ${group.location}. Points are separate observations; intervals are unobserved and no interpolation is drawn.`;section.append(detail);
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 700 220');svg.setAttribute('role','img');svg.setAttribute('aria-label',heading.textContent+' observations');
  const points=group.points,min=Date.parse(points[0].timestamp),span=Math.max(1,Date.parse(points.at(-1).timestamp)-min),max=Math.max(1,...points.map(p=>p.value));
  for(const p of points){const dot=document.createElementNS(svg.namespaceURI,'circle');dot.setAttribute('cx',String(30+640*(Date.parse(p.timestamp)-min)/span));dot.setAttribute('cy',String(190-160*p.value/max));dot.setAttribute('r','5');dot.setAttribute('fill',group.quality==='INVALID'?'#a34747':'#147c78');const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=`${p.timestamp}: ${p.value} ${group.unit}`;dot.append(title);svg.append(dot);}
  section.append(svg);target.append(section);
 }
}
