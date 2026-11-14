export function utcInput(value){
 if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?$/.test(value))throw Error('Enter an explicit valid UTC date and time.');
 const date=new Date(value+'Z');
 if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,16)!==value.slice(0,16))throw Error('Invalid UTC calendar date or time.');
 if(value.length>=19&&date.getUTCSeconds()!==Number(value.slice(17,19)))throw Error('Invalid UTC seconds.');
 return date.toISOString();
}
