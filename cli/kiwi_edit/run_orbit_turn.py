#!/usr/bin/env python3
from __future__ import annotations
import argparse,os,subprocess,tempfile
from pathlib import Path
import torch
from PIL import Image
from diffusers import DiffusionPipeline
from diffusers.utils import export_to_video

def load(path,max_frames,max_pixels):
 from torchvision.io import read_video
 vf,_,info=read_video(path,pts_unit='sec')
 fps=float(info.get('video_fps') or 24)
 out=[]
 for fr in vf[:max_frames]:
  im=Image.fromarray(fr.numpy());w,h=im.size;scale=min(1.0,(max_pixels/(w*h))**0.5)
  if scale<1:
   nw=max(16,int(w*scale)//16*16);nh=max(16,int(h*scale)//16*16);im=im.resize((nw,nh),Image.LANCZOS)
  out.append(im)
 return out,fps
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--shot-dir',required=True,help='directory holding your source plate and reference frame');ap.add_argument('--model',default='linyq/kiwi-edit-5b-instruct-reference-diffusers');ap.add_argument('--out');ap.add_argument('--steps',type=int,default=50);ap.add_argument('--seed',type=int,default=42);a=ap.parse_args()
 shot=Path(a.shot_dir);src=shot/'orbit_and_turn_4K8Bit_01.mov';ref=shot/'Orbit_and_turn_Firstframe_Flames_1088p_01.png';out=Path(a.out or shot/'OrbitTurn_Reskin/KiwiEdit/diagnostic_81f.mp4');out.parent.mkdir(parents=True,exist_ok=True)
 frames,fps=load(str(src),81,720*1280);h,w=frames[0].size[1],frames[0].size[0]
 pipe=DiffusionPipeline.from_pretrained(a.model,trust_remote_code=True);pipe.to('cuda:0',dtype=torch.bfloat16)
 prompt='Use the reference image as the appearance target for the source video. Keep the actor completely absent and preserve the altered wall, leaded window, sconce and photorealistic flame treatment. Retain the source camera path, acceleration, orbit, framing, perspective, parallax, timing and optical focus pull exactly. Maintain strict frame-to-frame geometry and texture identity; do not add people or objects.'
 video=pipe(prompt=prompt,source_video=frames,ref_image=[Image.open(ref).convert('RGB')],height=h,width=w,num_frames=len(frames),num_inference_steps=a.steps,guidance_scale=5.0,seed=a.seed,tiled=True)
 with tempfile.TemporaryDirectory() as td:
  silent=Path(td)/'silent.mp4';export_to_video(video,str(silent),fps=fps)
  cmd=['ffmpeg','-y','-i',str(silent),'-i',str(src),'-map','0:v:0','-map','1:a?','-c:v','copy','-c:a','aac','-shortest',str(out)]
  subprocess.run(cmd,check=True)
 print(out)
if __name__=='__main__':main()
