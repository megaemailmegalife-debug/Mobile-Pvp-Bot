import numpy as np
from scipy import signal
from scipy.io import wavfile
import os,json
SR=48000;DURATION=160.0;N=int(DURATION*SR)
rng=np.random.default_rng(1937);mix=np.zeros((N,2),np.float32);send=np.zeros_like(mix)
def add(x,start,gain=1,pan=0,wet=.15):
    i=int(round(start*SR))
    if i>=N:return
    if i<0:x=x[-i:];i=0
    x=np.asarray(x,np.float32);n=min(len(x),N-i)
    if n<=0:return
    lr=np.array([np.cos((pan+1)*np.pi/4),np.sin((pan+1)*np.pi/4)],np.float32)
    a=x[:n,None]*lr*gain;mix[i:i+n]+=a;send[i:i+n]+=a*wet
def note(midi,dur=.32,kind='pluck',vel=1):
    t=np.arange(int((dur+.22)*SR))/SR;f=440*2**((midi-69)/12);atk=1-np.exp(-t/.004)
    if kind=='bell':
        s=np.sin(2*np.pi*f*t+2.4*np.sin(2*np.pi*f*2*t)*np.exp(-t*8))*np.exp(-t*4)
        s+=.25*np.sin(2*np.pi*f*3.01*t)*np.exp(-t*11)
    elif kind=='pluck':
        s=np.zeros_like(t)
        for k in range(1,8):s+=np.sin(2*np.pi*f*k*t+.12*k)/k**1.3*np.exp(-t*(5+k*2))
        s+=.12*np.sin(2*np.pi*f*.5*t)*np.exp(-t*6)
    elif kind=='lead':
        s=np.zeros_like(t)
        for cents in [-.004,0,.004]:
            for k in range(1,9):s+=np.sin(2*np.pi*f*(1+cents)*k*t)/(k**1.55)*np.exp(-t*k*.8)/3
        s=np.tanh(s*1.4)*np.exp(-t*1.8)
    elif kind=='bass':
        s=np.sin(2*np.pi*f*t)*.8+np.sin(2*np.pi*f*2*t)*.22+np.sin(2*np.pi*f*3*t)*.12
        s=np.tanh(s*1.4)*np.exp(-t*4)
    elif kind=='pad':
        s=np.zeros_like(t)
        for k in range(1,6):s+=(np.sin(2*np.pi*f*k*t)+np.sin(2*np.pi*f*k*1.002*t))/(k*k)*.5
        atk=1-np.exp(-t/.18);s*=.65+.35*np.sin(2*np.pi*.16*t)
    else:s=np.sin(2*np.pi*f*t)*np.exp(-t*3)
    env=atk*np.minimum(1,np.maximum(0,(dur+.18-t)/.2))
    return (s*env*vel).astype(np.float32)
def kick():
    t=np.arange(int(.42*SR))/SR;phase=2*np.pi*(48*t+95*.026*(1-np.exp(-t/.026)))
    x=np.sin(phase)*np.exp(-t*11)+rng.normal(0,.14,len(t))*np.exp(-t*180)
    return np.tanh(x*1.7)*.78
def clap():
    t=np.arange(int(.28*SR))/SR;noise=rng.standard_normal(len(t))
    noise=signal.sosfilt(signal.butter(2,1300,'high',fs=SR,output='sos'),noise);env=np.exp(-t*25)
    for st in [.009,.019,.031]:env+=np.where(t>=st,np.exp(-np.maximum(0,t-st)*100),0)*.75
    return noise*env*.18
def hat(opened=False):
    t=np.arange(int((.23 if opened else .085)*SR))/SR;n=rng.standard_normal(len(t))
    n=signal.sosfilt(signal.butter(2,7000,'high',fs=SR,output='sos'),n)
    return n*np.exp(-t*(21 if opened else 75))*.14
def tom(f=160):
    t=np.arange(int(.28*SR))/SR
    return np.sin(2*np.pi*(f*t+f*.02*(1-np.exp(-t/.02))))*np.exp(-t*14)*.4
K=kick();C=clap();H=hat();OH=hat(True)
# Public-domain Grieg melodic material; new synthesized performance and arrangement.
A=[(59,.5),(61,.5),(62,.5),(64,.5),(66,.5),(62,.5),(66,1),
(65,.5),(61,.5),(65,1),(64,.5),(60,.5),(64,1),
(59,.5),(61,.5),(62,.5),(64,.5),(66,.5),(62,.5),(66,.5),(71,.5),
(69,.5),(66,.5),(62,.5),(66,.5),(71,1),(71,1)]
B=[(66,.5),(68,.5),(70,.5),(71,.5),(73,.5),(70,.5),(73,1),
(74,.5),(70,.5),(74,1),(73,.5),(70,.5),(73,1),
(66,.5),(68,.5),(70,.5),(71,.5),(73,.5),(70,.5),(73,1),
(74,.5),(70,.5),(74,1),(73,1),(73,1)]
for cycle in range(10):
    base=cycle*16
    if cycle==0:level=.25;kind='bell';octave=-12
    elif cycle==1:level=.40;kind='pluck';octave=0
    elif cycle in [2,3,4]:level=.42;kind='pluck';octave=0
    elif cycle==5:level=.31;kind='bell';octave=0
    elif cycle==6:level=.35;kind='pluck';octave=0
    else:level=.42;kind='lead';octave=0
    for p,phrase in enumerate([A,B]):
        b=0
        for j,(m,d) in enumerate(phrase):
            st=base+p*8+b*.5
            if st>=152:break
            if cycle==0 and st<4 and j>6:b+=d;continue
            add(note(m+octave,d*.5*.83,kind),st,level*(1 if j%3 else 1.08),.15*np.sin(j),.20)
            if cycle in [3,4,7,8,9]:add(note(m+12,d*.5*.7,'bell'),st,.09,-.32,.25)
            b+=d
for bar in range(76):
    st=bar*2;local=bar%8
    if local<4:roots=[35,37,35,35];chords=[[59,62,66],[61,65,68],[59,62,66],[59,62,66]]
    else:roots=[42,42,42,42];chords=[[58,61,66],[58,61,66],[58,61,66],[58,61,66]]
    root=roots[local%4];ch=chords[local%4];breakdown=44<=bar<52;intro=bar<8
    if bar>=4:
        for b in ([0,2] if intro or breakdown else [0,.75,1.5,2,2.75,3.5]):
            add(note(root-(1 if local==1 and b>=2 else 0)+(12 if b==2.75 else 0),.23,'bass'),st+b*.5,.27 if breakdown else .4,0,.04)
    if bar>=12:
        for off in ([0] if breakdown else [.5,1.5,2.5,3.5]):
            for m in ([60,64,67] if local==1 and off>=2 else ch):
                add(note(m,.16 if not breakdown else 1.5,'pad' if breakdown else 'pluck'),st+off*.5,.085 if breakdown else .10,(m%3-1)*.45,.36)
    if bar>=8 and not breakdown:
        for b in range(4):
            gain=.63 if bar<12 else .9
            if bar in [59,75] and b==3:continue
            add(K,st+b*.5,gain,0,.015)
            if b in [1,3]:add(C,st+b*.5,.72 if bar<28 else .95,0,.12)
        for h in range(8):
            ht=st+h*.25+(.018 if h%2 else 0)
            add(OH if h%2 else H,ht,.45 if h%2==0 else .8,(-1 if h%2 else 1)*.4,.07)
        if bar>=28 and bar%4==3:
            for h in range(4):add(H,st+1.5+h*.125,.45,.6,.08)
        if bar%8==7:
            for h in range(4):add(tom(160-h*18),st+1.5+h*.125,.44,.6-h*.35,.18)
    elif breakdown:
        if bar%2==0:add(K,st,.6,0,.14)
        add(H,st+1,.4,.5,.15)
    if bar<12 or breakdown or bar>=68:
        for b in range(4):add(note(95 if b%2 else 90,.025,'bell'),st+b*.5,.07,.55 if b%2 else -.55,.08)
    if 60<=bar<76:
        for eighth in range(8):
            m=[71,74,78,81,78,74,71,66][eighth]
            if local>=4:m+=7
            add(note(m,.1,'pluck'),st+eighth*.25,.07,np.sin(eighth*1.8)*.65,.35)
for at in [24,56,88,104,120,136]:
    length=3.8;t=np.arange(int(length*SR))/SR;noise=rng.standard_normal(len(t)).astype(np.float32)
    noise=signal.sosfilt(signal.butter(2,[1100,8500],'band',fs=SR,output='sos'),noise)
    add(noise*(t/length)**2*.095,at-length,1,-.12,.32)
    t2=np.arange(int(1.6*SR))/SR;crash=rng.standard_normal(len(t2))*np.exp(-t2*4)*.15
    crash=signal.sosfilt(signal.butter(2,4500,'high',fs=SR,output='sos'),crash);add(crash,at,.7,.2,.35)
for j in range(32):add(C,116+j*.125,.13+.30*j/32,.2*np.sin(j),.18)
for st,m in [(152,71),(152.5,66),(153,62),(153.5,66),(154,71)]:
    for octave,gain,kind in [(0,.4,'lead'),(-24,.35,'bass'),(12,.12,'bell')]:
        add(note(m+octave,1.0 if st==154 else .3,kind),st,gain,0,.3)
    if st<154:add(K,st,.75,0,.04)
for m in [47,59,62,66,71]:add(note(m,2.0,'pad'),154,.14,(m%3-1)*.3,.4)
add(note(83,.7,'bell'),157,.16,.25,.3)
for delay,gain,swap in [(.173,.22,True),(.257,.19,False),(.389,.14,True),(.521,.11,False),(.733,.07,True),(.947,.05,False)]:
    d=int(delay*SR);s=send[:-d,::-1] if swap else send[:-d];mix[d:]+=s*gain
mix=signal.sosfilt(signal.butter(2,28,'high',fs=SR,output='sos'),mix,axis=0).astype(np.float32)
mix=np.tanh(mix*1.14);mix*=.92/max(float(np.max(np.abs(mix))),.001)
mix[:int(.08*SR)]*=np.linspace(0,1,int(.08*SR))[:,None]
mix[-int(1.5*SR):]*=np.linspace(1,0,int(1.5*SR))[:,None]
out=os.path.join(os.path.dirname(__file__),'output');os.makedirs(out,exist_ok=True)
wavfile.write(os.path.join(out,'clockwork-rebellion.wav'),SR,(mix*32767).astype(np.int16))
print(json.dumps({'duration':DURATION,'sample_rate':SR,'peak_dbfs':float(20*np.log10(np.max(np.abs(mix)))),'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(mix**2))))}))
