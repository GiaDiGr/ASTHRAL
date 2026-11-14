from pathlib import Path
import sys,json,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'engine'))
from vigile.voice import LocalVoice
from vigile.english import assistant_name_alias
voice=LocalVoice();start=time.perf_counter()
try:
 status=voice.status();raw,tts=voice.synthesize('ASTHRAL, what is my recorded baseline?','en');transcript=voice.transcribe(raw,'en')
 report={'automated_synthetic_SAPI_to_Vosk_test':True,'human_microphone_used':False,'human_listening_acceptance':False,'text':'ASTHRAL, what is my recorded baseline?','raw_transcript':transcript['text'],'name_alias_result':assistant_name_alias(transcript['text']),'stt_model':transcript['model'],'tts_voice':tts['voice'],'transcription_seconds':transcript['transcription_seconds'],'synthesis_seconds':tts['synthesis_seconds'],'audio_written_to_disk':False,'total_seconds':time.perf_counter()-start}
except Exception as e:report={'automated_synthetic_SAPI_to_Vosk_test':False,'reason':str(e),'human_microphone_used':False,'human_listening_acceptance':False}
finally:voice.close()
(R/'docs/asthral/voice-smoke.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))