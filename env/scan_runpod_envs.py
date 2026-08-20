#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
REQ=json.load(open(HERE/'config/fit_requirements.json'))
SKIP={'proc','sys','dev','.cache','node_modules','.git','outputs','output'}
def limited_walk(root,maxdepth=5):
 root=Path(root)
 if not root.exists():return
 base=len(root.parts)
 for dp,dn,fn in os.walk(root):
  p=Path(dp); depth=len(p.parts)-base
  dn[:]=[d for d in dn if d not in SKIP and depth<maxdepth]
  yield p,dn,fn
def comfy_roots():
 out=set()
 for base in ['/workspace','/opt','/root']:
  for p,dn,fn in limited_walk(base,4) or []:
   if 'main.py' in fn and (p/'custom_nodes').is_dir() and (p/'models').is_dir():out.add(p)
 return sorted(out)
def cli_roots():
 out=set()
 for base in ['/workspace','/opt','/root']:
  for p,dn,fn in limited_walk(base,4) or []:
   low={x.lower() for x in fn}
   if 'diffusers_demo.py' in low or (p/'src/ltx_pipelines').exists() or (p/'ltx_pipelines').exists():out.add(p)
 return sorted(out)
def python_for(root):
 # A venv's own root can BE root/pyvenv.cfg (interpreter at root/bin/python), not always nested
 # under root/venv/. Missing this form sent the scanner to sys.executable (bare system python3.8,
 # no torch) for roots that actually have a perfectly good project-local torch+CUDA interpreter --
 # a false "no torch" reading, not a real gap (confirmed live on a real project ComfyUI root).
 for r in [root/'venv/bin/python',root/'.venv/bin/python',root/'env/bin/python',root/'python/bin/python']:
  if r.exists():return r
 if (root/'pyvenv.cfg').exists() and (root/'bin/python').exists():return root/'bin/python'
 return Path(sys.executable)
def pyinfo(py):
 code='import json,sys; d={"python":".".join(map(str,sys.version_info[:3]))};\ntry:\n import torch; d.update(torch=getattr(torch,"__version__",None),cuda=getattr(torch.version,"cuda",None))\nexcept Exception as e:d["torch_error"]=str(e)\nfor m in ["transformers","diffusers","accelerate"]:\n try:\n  x=__import__(m);d[m]=getattr(x,"__version__",None)\n except Exception:pass\nprint(json.dumps(d))'
 # 20s is too tight for a cold first `import torch` on a heavy CUDA venv (mmapping a large
 # libtorch/cudnn .so can take well past that) -- that previously surfaced as a subprocess
 # timeout and got folded into the same bucket as "torch really is missing", a false-failure
 # reading (T-INFRA-05: env-mismatch/slow-probe signatures are inconclusive, not a resource fact).
 # Confirmed live: ComfyUI_LTX23 and ComfyUI_SCAIL2 both timed out here yet have working
 # torch+CUDA when probed directly with more headroom.
 try:return json.loads(subprocess.check_output([str(py),'-c',code],text=True,stderr=subprocess.DEVNULL,timeout=90))
 except subprocess.TimeoutExpired:return {'inconclusive':'pyinfo probe timed out after 90s -- re-check manually with more headroom, do not treat as torch-missing'}
 except Exception as e:return {'error':str(e)}
def custom_markers(root):
 c=root/'custom_nodes';out=[]
 if c.exists():
  for p in c.iterdir():
   if p.is_dir():
    s=p.name
    cfg=p/'.git/config'
    if cfg.exists():
     try:s+=' '+cfg.read_text(errors='ignore')
     except:pass
    out.append(s.lower())
 return out
def file_index(root):
 pats=[]
 candidates=[root/'models',root/'checkpoints',root]
 for c in candidates:
  if not c.exists():continue
  for p,dn,fn in limited_walk(c,4) or []:
   for f in fn:
    if f.lower().endswith(('.safetensors','.pt','.pth','.bin','.json','.yaml','.yml')):pats.append(str((p/f).relative_to(root)).lower())
   if len(pats)>20000:return pats
 return pats
def version_score(actual,ideal):
 if not ideal:return 0
 if not actual:return -2
 return 3 if str(actual).startswith(str(ideal)) else -1
def score_env(tool,root,kind):
 spec=REQ[tool];py=python_for(root);info=pyinfo(py);marks=custom_markers(root) if kind=='comfyui' else []
 idx=file_index(root); joined='\n'.join(marks+idx+[str(root).lower()])
 score=0;missing=[];present=[]
 for m in spec.get('required_custom_node_markers',[]):
  if m.lower() in joined:score+=8;present.append(m)
  else:missing.append('node:'+m)
 for m in spec.get('useful_custom_node_markers',[]):
  if m.lower() in joined:score+=2;present.append(m)
 for m in spec.get('required_repo_markers',[]):
  if m.lower() in joined or (root/m).exists():score+=8;present.append(m)
  else:missing.append('repo:'+m)
 for m in spec.get('required_model_patterns',[]):
  if m.lower() in joined:score+=5;present.append(m)
  else:missing.append('model:'+m)
 score+=version_score(info.get('python'),spec.get('ideal_python'))+version_score(info.get('torch'),spec.get('ideal_torch'))+version_score(info.get('cuda'),spec.get('ideal_cuda'))+version_score(info.get('transformers'),spec.get('ideal_transformers'))
 if str(root) in spec.get('preferred_roots',[]):score+=15
 status='safe_reuse' if not missing else ('install_nodes_or_models_only' if score>=12 else 'bespoke_required')
 return {'tool':tool,'root':str(root),'kind':kind,'python_executable':str(py),'runtime':info,'score':score,'status':status,'present':present,'missing':missing,'notes':spec.get('notes')}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='env_fit_report');a=ap.parse_args()
 cs=comfy_roots();ls=cli_roots();allres={}
 for tool,s in REQ.items():
  roots=cs if s['kind']=='comfyui' else ls
  # Include preferred paths even if scanner did not classify them yet.
  roots=sorted(set(roots+[Path(x) for x in s.get('preferred_roots',[]) if Path(x).exists()]))
  rows=sorted([score_env(tool,r,s['kind']) for r in roots],key=lambda x:x['score'],reverse=True)
  allres[tool]={'best':rows[0] if rows else None,'candidates':rows,'leftover':None if rows and rows[0]['status']!='bespoke_required' else 'No sufficiently compatible existing environment found; create an isolated environment.'}
 out=Path(a.out);out.with_suffix('.json').write_text(json.dumps(allres,indent=2))
 md=['# RunPod environment-fit report','']
 for t,v in allres.items():
  md+=['## '+t]
  if not v['best']:md+=['No candidate root found. **Bespoke environment required.**',''];continue
  b=v['best'];md += [f"Best: `{b['root']}`",f"Status: **{b['status']}**; score {b['score']}",f"Python: `{b['python_executable']}`; runtime: `{json.dumps(b['runtime'])}`",f"Missing: `{', '.join(b['missing']) or 'none detected'}`",b['notes'],'']
 out.with_suffix('.md').write_text('\n'.join(md))
 print('\n'.join(md))
if __name__=='__main__':main()
