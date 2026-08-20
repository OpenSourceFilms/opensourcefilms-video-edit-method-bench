#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument('report');ap.add_argument('--out',default='leftovers/LEFTOVERS_RUNTIME.md');a=ap.parse_args();d=json.load(open(a.report))
 lines=['# Runtime leftovers','']
 any_left=False
 for tool,v in d.items():
  b=v.get('best')
  if not b or b.get('status')=='bespoke_required':
   any_left=True;lines+=['## '+tool]
   if not b:lines+=['No candidate environment was discovered.','']
   else:
    lines += [f"Best attempted root: `{b['root']}`",f"Runtime: `{json.dumps(b.get('runtime',{}))}`",f"Missing: `{', '.join(b.get('missing',[])) or 'none indexed'}`",f"Decision: **create a bespoke isolated environment**.",'']
 if not any_left:lines+=['No tool currently requires a bespoke environment according to the scanner. Missing model files or custom nodes may still need installation in otherwise compatible roots.','']
 Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text('\n'.join(lines));print('\n'.join(lines))
if __name__=='__main__':main()
