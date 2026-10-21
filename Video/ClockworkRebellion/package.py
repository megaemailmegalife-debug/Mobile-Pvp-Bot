import subprocess,json,hashlib,base64
from pathlib import Path
import numpy as np
from scipy.io import wavfile
ROOT=Path(__file__).parent
out=ROOT/'output'
parts=[out/f'part-{s}.mp4' for s in [0,40,80,120]]
for f in parts:
    if not f.exists() or f.stat().st_size<1000:raise RuntimeError(f'Missing rendered part: {f}')
(out/'concat.txt').write_text(''.join("file '"+str(f.resolve())+"'\n" for f in parts))
target=out/'Clockwork-Rebellion.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(out/'concat.txt'),'-i',str(out/'clockwork-rebellion.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-metadata','title=Clockwork Rebellion','-metadata','artist=Original 3D animation and electronic arrangement','-metadata','comment=Music: Edvard Grieg, In the Hall of the Mountain King, public-domain composition. New synthesized recording; no commercial samples.','-movflags','+faststart','-shortest',str(target)],check=True)
data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(target)]))
v=next(x for x in data['streams'] if x['codec_type']=='video')
a=next(x for x in data['streams'] if x['codec_type']=='audio')
assert v['width']==1920 and v['height']==1080
assert abs(float(data['format']['duration'])-160)<.1
assert int(v['nb_frames'])==3840
assert a['channels']==2
subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True)
sr,w=wavfile.read(out/'clockwork-rebellion.wav');wf=w.astype(np.float32)/32768
assert len(w)/sr==160 and np.max(np.abs(wf))<.99 and np.sqrt(np.mean(wf**2))>.015
report={'title':'Clockwork Rebellion','duration_seconds':float(data['format']['duration']),'dimensions':[v['width'],v['height']],'frames':int(v['nb_frames']),'frame_rate':v['r_frame_rate'],'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'audio_channels':a['channels'],'sample_rate':a['sample_rate'],'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'full_decode':'passed','soundtrack_peak_dbfs':float(20*np.log10(np.max(np.abs(wf)))),'soundtrack_rms_dbfs':float(20*np.log10(np.sqrt(np.mean(wf**2)))),'music_source':'Public-domain Grieg composition; new mathematical synthesis, no third-party recording or samples.'}
(out/'verification.json').write_text(json.dumps(report,indent=2))
print('VERIFIED_VIDEO '+json.dumps(report),flush=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','129','-i',str(target),'-frames:v','1','-vf','scale=960:-1','-q:v','3',str(out/'final-review.jpg')],check=True)
print('FINAL_FRAME_BASE64_BEGIN'+base64.b64encode((out/'final-review.jpg').read_bytes()).decode()+'FINAL_FRAME_BASE64_END',flush=True)
