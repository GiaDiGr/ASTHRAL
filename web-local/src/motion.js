export const POSE_JOINTS={left_elbow:[11,13,15],right_elbow:[12,14,16],left_knee:[23,25,27],right_knee:[24,26,28]};
export function projectedAngle(points,indices,width,height,minimumVisibility=.5){
 if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0||!Number.isFinite(minimumVisibility)||minimumVisibility<0||minimumVisibility>1||!Array.isArray(points))return null;
 const p=indices.map(i=>points[i]);if(p.some(v=>!v||!Number.isFinite(v.x)||!Number.isFinite(v.y)||v.x<0||v.x>1||v.y<0||v.y>1||!Number.isFinite(v.visibility)||v.visibility<minimumVisibility||v.visibility>1))return null;
 const [a,b,c]=p,u=[(a.x-b.x)*width,(a.y-b.y)*height],v=[(c.x-b.x)*width,(c.y-b.y)*height],norm=Math.hypot(...u)*Math.hypot(...v);if(norm<1e-9)return null;
 return Math.acos(Math.max(-1,Math.min(1,(u[0]*v[0]+u[1]*v[1])/norm)))*180/Math.PI;
}
export class CycleCounter{
 constructor(low,high){if(!Number.isFinite(low)||!Number.isFinite(high)||low<0||high>180||low>=high)throw Error('CYCLE_LIMITS_INVALID');this.low=low;this.high=high;this.phase='WAIT_HIGH';this.count=0;}
 update(angle){if(!Number.isFinite(angle)){this.phase='WAIT_HIGH';return this.count;}if(this.phase==='WAIT_HIGH'&&angle>=this.high)this.phase='WAIT_LOW';else if(this.phase==='WAIT_LOW'&&angle<=this.low)this.phase='WAIT_RETURN';else if(this.phase==='WAIT_RETURN'&&angle>=this.high){this.count++;this.phase='WAIT_LOW';}return this.count;}
}
export class PoseClient{
 constructor(){this.serial=0;this.closed=false;this.pending=new Map();this.worker=new Worker('./motion-worker.js');this.worker.onmessage=({data})=>{const task=this.pending.get(data.id);if(!task)return;this.pending.delete(data.id);clearTimeout(task.timer);data.error?task.reject(Error(data.error)):task.resolve(data.result);};this.worker.onerror=()=>this.close();}
 call(action,data={},transfer=[]){if(this.closed)return Promise.reject(Error('POSE_WORKER_STOPPED'));return new Promise((resolve,reject)=>{const id=++this.serial;const timer=setTimeout(()=>{this.close();},action==='install'?120000:15000);this.pending.set(id,{resolve,reject,timer});try{this.worker.postMessage({id,action,...data},transfer);}catch(error){clearTimeout(timer);this.pending.delete(id);reject(error);}});}
 close(){if(this.closed)return;this.closed=true;this.worker?.terminate();this.worker=null;for(const task of this.pending.values()){clearTimeout(task.timer);task.reject(Error('POSE_WORKER_STOPPED'));}this.pending.clear();}
}
