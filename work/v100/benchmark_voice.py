"""Explicit synthetic SAPI reference corpus; never records a microphone.
Reference text is authored before transcription and never derived from predictions.
"""
from pathlib import Path
import sys,json,time,re,unicodedata,io,wave,random,array,os
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'engine'))
from vigile.voice import LocalVoice,VoiceError
from vigile.space_compute import process_resources,telemetry
refs={'en':['Microgravity.','Hypoglycemia.','Diabetic ketoacidosis.','Orthostatic hypotension.','Radiation exposure.','Heart rate.','Personal baseline.','Potassium.','Oxygen saturation.','VIGILE, how has my physical condition changed during the mission?','VIGILE, why am I receiving this medical alert?','What information is missing from my evaluation?','Glucose is one hundred eighty milligrams per deciliter.','Venous p H is seven point two two.','Treatment is not authorized. The protocol is blocked.','A missing measurement is not a normal result.'],
'es':['Microgravedad.','Hipoglucemia.','Cetoacidosis diabética.','Hipotensión ortostática.','Exposición a radiación.','Frecuencia cardíaca.','Valor basal personal.','Potasio.','Saturación de oxígeno.','VIGILE, cómo cambió mi condición física durante la misión?','VIGILE, por qué recibo esta alerta médica?','Qué cambió desde mi última evaluación?','La glucosa es ciento ochenta miligramos por decilitro.','El p H venoso es siete coma veintidós.','El tratamiento no está autorizado. El protocolo está bloqueado.','Un dato ausente no es un resultado normal.']}
out=ROOT/'docs/v100/voice-benchmark';out.mkdir(exist_ok=False)
(out/'references.json').write_text(json.dumps(refs,indent=2,ensure_ascii=False),encoding='utf8')
def words(s):return re.findall(r'\w+',unicodedata.normalize('NFC',s.lower()))
def edit(a,b):
 row=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  new=[i]
  for j,y in enumerate(b,1):new.append(min(row[j]+1,new[-1]+1,row[j-1]+(x!=y)))
  row=new
 return row[-1]
voice=LocalVoice();report={'corpus':'SYNTHETIC_INSTALLED_SAPI_NOT_HUMAN_MEDICAL_SPEECH','reference_independent_of_stt':True,'clinical_validation':False,'microphone_capture_latency':'NOT_MEASURED_BY_SYNTHETIC_CORPUS','power':'NOT_MEASURED','rows':[],'failures':[],'before':telemetry([os.getpid()])};cpu=time.process_time()
for language,phrases in refs.items():
 for i,text in enumerate(phrases):
  start=time.perf_counter();raw,tts=voice.synthesize(text,language);(out/(language+'-'+str(i)+'.wav')).write_bytes(raw)
  try:r=voice.transcribe(raw,language);predicted=r['text'];stt=r['transcription_seconds'];error=None
  except VoiceError as exc:predicted='';stt=None;error=str(exc)
  reference=words(text);prediction=words(predicted);distance=edit(reference,prediction)
  row={'language':language,'id':i,'reference':text,'prediction':predicted,'word_errors':distance,'reference_words':len(reference),'wer':distance/len(reference),'stt_seconds':stt,'tts':tts,'synthetic_audio_seconds':len(raw[44:])/32000,'roundtrip_seconds':time.perf_counter()-start,'error':error,'negation_review_required':('not' in reference and 'not' not in prediction) or ('no' in reference and 'no' not in prediction),'process':process_resources(os.getpid())};report['rows'].append(row)
  (out/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');print(language,i,round(row['wer'],3),flush=True)
# Negative/quality trials use known synthetic signals, not ambient recordings.
for label,raw,lang in [('empty',b'','en'),('corrupt',b'not audio','en'),('wrong-language',(out/'en-9.wav').read_bytes(),'es')]:
 try:r=voice.transcribe(raw,lang);report['failures'].append({'case':label,'recognized':r['text'],'review_required':True})
 except VoiceError as exc:report['failures'].append({'case':label,'rejected':str(exc)})
for label,values in [('silence',[0]*48000),('seeded-white-noise',[random.Random(i).randint(-1200,1200) for i in range(48000)])]:
 mem=io.BytesIO()
 with wave.open(mem,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(array.array('h',values).tobytes())
 try:r=voice.transcribe(mem.getvalue(),'en');report['failures'].append({'case':label,'recognized':r['text'],'possible_noise_false_positive':True,'review_required':True})
 except VoiceError as exc:report['failures'].append({'case':label,'rejected':str(exc)})
report['after']=telemetry([os.getpid()]);report['cpu_seconds']=time.process_time()-cpu;report['summary']={language:{'utterances':len([r for r in report['rows'] if r['language']==language]),'corpus_wer':sum(r['word_errors'] for r in report['rows'] if r['language']==language)/sum(r['reference_words'] for r in report['rows'] if r['language']==language),'exact_transcripts':sum(r['wer']==0 for r in report['rows'] if r['language']==language),'negation_flags':sum(r['negation_review_required'] for r in report['rows'] if r['language']==language)} for language in refs}
(out/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');voice.close();print(json.dumps(report['summary'],indent=2))