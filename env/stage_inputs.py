#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, shutil
from pathlib import Path
FILES=[
 'orbit_and_turn_4K8Bit_01.mov',
 'Orbit_and_turn_Firstframe_Flames_1088p_01.png',
 'Orbit_and_turn_Middleframe_Flames_1088p_02.png',
 'Orbit_and_turn_Lastframe_Flames_1088p_02.png']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--comfy-root',required=True);ap.add_argument('--shot-dir',required=True,help='directory holding your source plate and reference frames');ap.add_argument('--copy',action='store_true',help='copy instead of symlink');a=ap.parse_args()
 src=Path(a.shot_dir);dst=Path(a.comfy_root)/'input';dst.mkdir(parents=True,exist_ok=True)
 for name in FILES:
  s=src/name;d=dst/name
  if not s.exists():raise FileNotFoundError(s)
  if d.exists() or d.is_symlink():
   if d.resolve()==s.resolve():print('OK',d);continue
   raise FileExistsError(f'{d} exists and does not point to {s}')
  if a.copy:shutil.copy2(s,d)
  else:d.symlink_to(s)
  print(('COPIED' if a.copy else 'LINKED'),d,'->',s)
if __name__=='__main__':main()
