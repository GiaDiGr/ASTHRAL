"""Genuine browser pose inference using licensed local video fixtures; no profile writes."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8942/');parser.add_argument('--output',default='work/browser-pose-acceptance');args=parser.parse_args();root=Path(__file__).resolve().parents[1];out=(root/args.output).resolve();out.mkdir(parents=True,exist_ok=True)
report={'status':'FAILED','errors':[],'fixtures':[],'codec_support':{}}
def capture(**options):
 try:page.screenshot(timeout=5000,**options)
 except Exception as error:report.setdefault('capture_errors',[]).append(str(error))
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=str(next((Path.home()/'AppData/Local/ms-playwright/chromium-1181').rglob('chrome.exe'))));page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:report['errors'].append(str(e)))
 try:
  page.goto(args.url);report['codec_support']=page.evaluate('''()=>{const v=document.createElement('video');return {h264:v.canPlayType('video/mp4; codecs=avc1.42E01E'),vp8:v.canPlayType('video/webm; codecs=vp8')};}''');expect(page.locator('#runtime-status')).to_contain_text('ready on this device',timeout=60000);page.locator('#explore').click();expect(page.locator('#operation')).to_contain_text('Temporary synthetic demo ready',timeout=30000);page.locator('#workspace-nav .more-nav > summary').click();page.locator('#workspace-nav [data-view="exercise"]').click();section=page.locator('#motionguard')
  for name,joint in [('wall-push','left_elbow'),('knee-pushups','left_elbow'),('squat','left_knee')]:
   section.get_by_label('Licensed prerecorded test video (temporary demo only)',exact=True).select_option(name);section.get_by_role('button',name='Use licensed test video (demo)',exact=True).click()
   section.get_by_role('button',name='Load verified pose model (CPU)',exact=True).click();section.get_by_text('Ready: MediaPipe Pose Landmarker Lite',exact=False).wait_for(timeout=60000);print('MODEL_READY',name,report['codec_support'],flush=True);section.get_by_label('Projected joint to track',exact=True).select_option(joint)
   section.get_by_label('Optional lower cycle boundary (degrees, technical setting)',exact=True).fill('70');section.get_by_label('Optional upper cycle boundary (degrees, technical setting)',exact=True).fill('150');expect(section.locator('video')).to_have_js_property('readyState',4,timeout=10000);section.get_by_role('button',name='Analyze local video',exact=True).click();expect(section.get_by_role('button',name='Analyze local video',exact=True)).to_be_enabled(timeout=90000);print('ANALYSIS_STATE',section.locator('[role=status]').inner_text(),flush=True);assert section.locator('[role=status]').inner_text().startswith('Analysis completed.')
   with page.expect_download() as event:section.get_by_role('button',name='Export pose analysis (plaintext JSON)',exact=True).click()
   actual=json.loads(Path(event.value.path()).read_text());assert actual['frames'];assert all(r['angle_degrees'] is None or 0<=r['angle_degrees']<=180 for r in actual['frames']);assert actual['summary']['model']['delegate']=='CPU';assert actual['summary']['cycles'] is None if actual['summary']['missing_angle_frames'] else True;(out/(name+'.json')).write_text(json.dumps(actual,indent=2));report['fixtures'].append({'name':name,'summary':actual['summary'],'reference_cycle_count':None,'accuracy_validated':False});capture(path=str(out/(name+'.png')),full_page=True)
  report['status']='GENUINE_INFERENCE_EXECUTED_NOT_BIOMECHANICAL_VALIDATION'
 except Exception as error:report['failure']=str(error);capture(path=str(out/'failure.png'),full_page=True)
 finally:(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True);b.close()



if report["status"] in {"FAILED","NOT_COMPLETED"}:raise SystemExit(1)
