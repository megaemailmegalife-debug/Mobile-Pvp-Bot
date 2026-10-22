import os,json,time,subprocess,shutil,tempfile,base64,hashlib
from pathlib import Path
import requests
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import hashes
REPO=os.environ["GITHUB_REPOSITORY"]
BRANCH="codex/clockwork-rebellion-video-20261021"
RUN=os.environ["GITHUB_RUN_ID"]
ROOT=Path.cwd()
API="https://api.github.com/repos/"+REPO
SESSION=requests.Session()
SESSION.headers.update({"Authorization":"Bearer "+os.environ["GITHUB_TOKEN"],"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
def get_file(path):
 r=SESSION.get(API+"/contents/"+path,params={"ref":BRANCH},timeout=30)
 if r.status_code==404:return None
 r.raise_for_status()
 return base64.b64decode(r.json()["content"])
def put_file(path,content,message):
 current=SESSION.get(API+"/contents/"+path,params={"ref":BRANCH},timeout=30)
 body={"message":message+" [skip ci]","branch":BRANCH,"content":base64.b64encode(content).decode()}
 if current.ok:body["sha"]=current.json()["sha"]
 elif current.status_code!=404:current.raise_for_status()
 r=SESSION.put(API+"/contents/"+path,json=body,timeout=60)
 r.raise_for_status()
 return r.json()["commit"]["sha"]
key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
pub=key.public_key().public_numbers()
keyid=os.urandom(16).hex()
public={"run_id":RUN,"key_id":keyid,"n":format(pub.n,"x"),"e":pub.e,"algorithm":"RSA-OAEP-SHA256","expires_in_seconds":600}
put_file("SitesSupport/public-key.json",json.dumps(public).encode(),"Publish ephemeral Site transfer public key")
print("PUBLIC_KEY_READY "+RUN,flush=True)
envelope=None
for attempt in range(120):
 data=get_file("SitesSupport/envelope.json")
 if data:
  candidate=json.loads(data)
  if candidate.get("key_id")==keyid:
   envelope=candidate
   break
 time.sleep(5)
if envelope is None:raise RuntimeError("No encrypted deployment credential received before timeout")
plaintext=b"".join(key.decrypt(bytes.fromhex(chunk),padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None)) for chunk in envelope["chunks"])
credential=json.loads(plaintext)
token=credential.pop("token")
# The credential stays in memory and child-process environment only.
# Suppress Git output so server diagnostics cannot echo a credential.
env=os.environ.copy()
env.update({"GIT_TERMINAL_PROMPT":"0","GIT_CONFIG_COUNT":"1","GIT_CONFIG_KEY_0":"http.extraheader","GIT_CONFIG_VALUE_0":"Authorization: Bearer "+token})
remote=credential["remote_url"]
assert remote.startswith("https://git.chatgpt-team.site/") and remote.endswith(".git")
work=Path(tempfile.mkdtemp(prefix="clockwork-site-"))
def git(*args):
 p=subprocess.run(["git",*args],cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:
  safe=(p.stdout+p.stderr).replace(token,"[redacted]")
  raise RuntimeError("Git command failed: "+safe[:3000])
 return p.stdout.strip()
git("init","--initial-branch="+credential["branch"])
git("remote","add","origin",remote)
refs=git("ls-remote","--heads","origin",credential["branch"])
if refs:
 git("fetch","--depth=1","origin",credential["branch"])
 git("checkout","-B",credential["branch"],"FETCH_HEAD")
src=ROOT/"Sites/ClockworkRebellion"
manifest=json.loads((src/".openai/hosting.json").read_text())
assert manifest["project_id"]==credential["repository"]
for name in [".openai","dist"]:
 dest=work/name
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(src/name,dest)
assert hashlib.sha256((work/"dist/clockwork-rebellion.mp4").read_bytes()).hexdigest()=="6e0572454b7cb5fb78881b13085d2660d44dd483d061572fe0ea135e7ecc290e"
git("config","user.name","Clockwork site builder")
git("config","user.email","clockwork-builder@users.noreply.github.com")
git("add",".openai/hosting.json","dist")
git("commit","-m","Publish complete Clockwork Rebellion music video player")
git("push","origin","HEAD:"+credential["branch"])
sha=git("rev-parse","HEAD")
result={"project_id":manifest["project_id"],"commit_sha":sha,"source_pushed":True,"video_bytes":(work/"dist/clockwork-rebellion.mp4").stat().st_size,"run_id":RUN}
env.pop("GIT_CONFIG_VALUE_0",None)
token=None
plaintext=None
credential=None
key=None
put_file("SitesSupport/deploy-result.json",json.dumps(result,indent=2).encode(),"Record verified Site source push")
print("SITES_SOURCE_PUSHED "+json.dumps(result),flush=True)
