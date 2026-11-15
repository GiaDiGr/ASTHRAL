export const RADIATION_CSV_COLUMNS=Object.freeze(['quantity_kind','value','unit','timestamp','mode','quality','mission_segment','location','source','instrument_id','uncertainty_value','uncertainty_unit','note']);

function rowsOf(text){
 if(typeof text!=='string'||text.length>5_000_000)throw Error('CSV file must be text no larger than 5 MB.');
 const rows=[];let row=[],cell='',quoted=false;
 for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c;}else if(c==='"'){if(cell)throw Error('CSV quote must begin an empty field.');quoted=true;}else if(c===','){row.push(cell);cell='';}else if(c==='\n'){row.push(cell.replace(/\r$/,''));cell='';if(row.some(v=>v.trim()))rows.push(row);row=[];}else cell+=c;}
 if(quoted)throw Error('CSV has an unterminated quoted field.');row.push(cell.replace(/\r$/,''));if(row.some(v=>v.trim()))rows.push(row);return rows;
}

export function parseRadiationCsv(text){
 const rows=rowsOf(text);if(!rows.length)throw Error('CSV is empty.');
 const header=rows.shift().map(v=>v.trim());if(new Set(header).size!==header.length)throw Error('CSV contains duplicate column names.');
 if(header.length!==RADIATION_CSV_COLUMNS.length||header.some((v,i)=>v!==RADIATION_CSV_COLUMNS[i]))throw Error(`CSV header must exactly match: ${RADIATION_CSV_COLUMNS.join(',')}`);
 if(!rows.length||rows.length>10000)throw Error('CSV must contain between 1 and 10000 records.');
 return rows.map((cells,index)=>{if(cells.length!==header.length)throw Error(`Row ${index+2} has ${cells.length} fields; expected ${header.length}.`);const raw=Object.fromEntries(header.map((name,i)=>[name,cells[i].trim()]));const out={quantity_kind:raw.quantity_kind,value:raw.value,unit:raw.unit,timestamp:raw.timestamp,mode:raw.mode,quality:raw.quality,mission_segment:raw.mission_segment,location:raw.location,source:raw.source,instrument_id:raw.instrument_id||null,note:raw.note};if(raw.uncertainty_value){out.uncertainty={value:raw.uncertainty_value,unit:raw.uncertainty_unit};}return out;});
}
