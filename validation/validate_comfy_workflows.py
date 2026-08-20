#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys,re
from pathlib import Path

def graphs(x):
 seen=set()
 def rec(v,path='$'):
  if id(v) in seen:return
  seen.add(id(v))
  if isinstance(v,dict):
   if isinstance(v.get('nodes'),list) and isinstance(v.get('links'),list):yield path,v
   for k,z in v.items():yield from rec(z,f'{path}.{k}')
  elif isinstance(v,list):
   for i,z in enumerate(v):yield from rec(z,f'{path}[{i}]')
 yield from rec(x)
def link_id(l):return l[0] if isinstance(l,list) else l.get('id')
def validate(path):
 d=json.load(open(path,encoding='utf-8'));errors=[];warnings=[];gcount=0
 for gp,g in graphs(d):
  gcount+=1; ns=g.get('nodes',[]);ls=g.get('links',[]);ids=[n.get('id') for n in ns]
  if len(ids)!=len(set(ids)):errors.append(f'{gp}: duplicate node IDs')
  lids=[link_id(l) for l in ls]
  if len(lids)!=len(set(lids)):errors.append(f'{gp}: duplicate link IDs')
  nd={n.get('id'):n for n in ns}
  for l in ls:
   if not isinstance(l,list) or len(l)<6: warnings.append(f'{gp}: nonstandard link object {l!r}');continue
   lid,oid,oslot,tid,tslot,_=l[:6]
   if oid not in nd or tid not in nd:errors.append(f'{gp}: link {lid} references missing node')
   else:
    if oslot>=len(nd[oid].get('outputs',[])):errors.append(f'{gp}: link {lid} bad origin slot')
    if tslot>=len(nd[tid].get('inputs',[])):errors.append(f'{gp}: link {lid} bad target slot')
  linkset=set(lids)
  for n in ns:
   for i in n.get('inputs',[]):
    if i.get('link') is not None and i['link'] not in linkset:errors.append(f'{gp}: node {n.get("id")} input points to absent link {i["link"]}')
 text=json.dumps(d,ensure_ascii=False)
 for bad in ('GunCatch','fight_test','FightTest'):
  if bad.lower() in text.lower():errors.append(f'forbidden leftover string: {bad}')
 if 'orbit_and_turn_4K8Bit_01.mov' not in text:warnings.append('Orbit source filename not found')
 return {'file':str(path),'graphs':gcount,'errors':errors,'warnings':warnings,'ok':not errors}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('paths',nargs='+');ap.add_argument('--report');a=ap.parse_args();files=[]
 for p in a.paths:
  q=Path(p);files.extend(sorted(q.rglob('*.json')) if q.is_dir() else [q])
 out=[validate(p) for p in files if p.name not in ('SOURCE_LOCK.json','orbit_turn.json','fit_requirements.json','WORKFLOW_MANIFEST.json')]
 print(json.dumps(out,indent=2));
 if a.report:Path(a.report).write_text(json.dumps(out,indent=2))
 sys.exit(1 if any(not x['ok'] for x in out) else 0)
if __name__=='__main__':main()
