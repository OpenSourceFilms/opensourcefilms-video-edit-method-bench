#!/usr/bin/env python3
"""Download current locked upstream ComfyUI workflows and make Orbit-and-Turn variants.
Topology is preserved. The script edits widgets/filenames and disconnects only optional inputs
whose mode does not use them. It fails if expected upstream node families are absent.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, sys, urllib.request
from pathlib import Path

SOURCE_VIDEO="orbit_and_turn_4K8Bit_01.mov"  # confirmed 2026-08-06: the real diagnostic-test proxy (264f/24fps/4096x2160,
# correct name) already lives in ComfyUI_LTX23/input/ -- the POC_VFX plate dir only has a .mp4 by
# this name, which is a DIFFERENT (unrelated) file; do not "fix" this back to .mp4 without re-checking.
FIRST="Orbit_and_turn_Firstframe_Flames_1088p_01.png"
EA_URL="https://huggingface.co/Alissonerdx/EditAnything/resolve/main/workflows/edit_anything_with_ref_or_motion_transfer_v0.1.json?download=true"
FLEX_URL="https://raw.githubusercontent.com/IGL-HKUST/FlexAM/main/assets/flexam_workflow.json"
DITTO_URL="https://raw.githubusercontent.com/EzioBy/Ditto/main/ditto_comfyui_workflow.json"
LOCKS={"flexam":"ae43d1c1164382298e55146625de6badd197364b","ditto":"773b74aafffba4268fa13b3218fa4ca14891b021"}

def git_blob_sha(b:bytes)->str: return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def download_json(url:str, expected_blob:str|None=None):
    req=urllib.request.Request(url,headers={"User-Agent":"OrbitTurn-workflow-materializer/1.0"})
    with urllib.request.urlopen(req,timeout=120) as r: b=r.read()
    if expected_blob and git_blob_sha(b)!=expected_blob:
        raise RuntimeError(f"Upstream blob changed: expected {expected_blob}, got {git_blob_sha(b)}. Inspect before continuing.")
    return json.loads(b), hashlib.sha256(b).hexdigest()

def graph_dicts(obj):
    seen=set()
    def rec(x):
        if id(x) in seen:return
        seen.add(id(x))
        if isinstance(x,dict):
            if isinstance(x.get('nodes'),list) and isinstance(x.get('links'),list): yield x
            for v in x.values(): yield from rec(v)
        elif isinstance(x,list):
            for v in x: yield from rec(v)
    yield from rec(obj)
def nodes(obj):
    for g in graph_dicts(obj):
        for n in g.get('nodes',[]): yield g,n

def set_input_widget(n,name,value):
    w=n.get('widgets_values')
    if isinstance(w,dict):
        if name in w: w[name]=value; return True
        return False
    if not isinstance(w,list): return False
    # Build the widget order from primitive, unlinked inputs. Some Comfy nodes add control_after_generate after seed.
    candidates=[]
    for i in n.get('inputs',[]):
        if i.get('link') is None and i.get('widget') is not None:
            candidates.append(i.get('name'))
    if name in candidates:
        idx=candidates.index(name)
        # Account for the common seed control widget.
        if 'seed' in candidates and idx>candidates.index('seed') and len(w)==len(candidates)+1: idx+=1
        if idx<len(w): w[idx]=value; return True
    return False

def set_load_video(n,frames):
    w=n.get('widgets_values')
    if isinstance(w,dict):
        w.update({'video':SOURCE_VIDEO,'force_rate':24,'frame_load_cap':frames,'skip_first_frames':0,'select_every_nth':1})
        p=((w.get('videopreview') or {}).get('params') or {})
        p.update({'filename':SOURCE_VIDEO,'force_rate':24,'frame_load_cap':frames,'skip_first_frames':0,'select_every_nth':1})
        return
    if isinstance(w,list):
        # VHS order: video, force_rate, width, height, cap, skip, nth, format
        if len(w)>=1:w[0]=SOURCE_VIDEO
        if len(w)>=2:w[1]=24
        if len(w)>=5:w[4]=frames
        if len(w)>=6:w[5]=0
        if len(w)>=7:w[6]=1

def set_load_image(n):
    w=n.get('widgets_values')
    if isinstance(w,dict):
        for k in ('image','filename'): 
            if k in w:w[k]=FIRST
    elif isinstance(w,list) and w:w[0]=FIRST

def set_text(n,text):
    w=n.get('widgets_values')
    if isinstance(w,dict):
        for k in ('text','prompt','value','string'):
            if k in w:w[k]=text;return True
    elif isinstance(w,list) and w and isinstance(w[0],str):w[0]=text;return True
    return False

def set_output(n,prefix):
    w=n.get('widgets_values')
    if isinstance(w,dict):
        for k,v in {'frame_rate':24,'filename_prefix':prefix,'crf':16,'save_output':True}.items():
            if k in w:w[k]=v
    else:
        set_input_widget(n,'frame_rate',24);set_input_widget(n,'filename_prefix',prefix);set_input_widget(n,'crf',16);set_input_widget(n,'save_output',True)

def remove_link(g,lid):
    if lid is None:return
    g['links']=[l for l in g.get('links',[]) if (l[0] if isinstance(l,list) else l.get('id'))!=lid]
    for n in g.get('nodes',[]):
        for i in n.get('inputs',[]):
            if i.get('link')==lid:i['link']=None
        for o in n.get('outputs',[]):
            if isinstance(o.get('links'),list):o['links']=[x for x in o['links'] if x!=lid]

def disconnect_input(g,n,names):
    for i in n.get('inputs',[]):
        if i.get('name','').lower() in {x.lower() for x in names}:
            remove_link(g,i.get('link'));i['link']=None

def bypass(n): n['mode']=4

def patch_common(obj,frames,prefix,positive,negative):
    counts={'video':0,'image':0,'output':0,'positive':0,'negative':0}
    for g,n in nodes(obj):
        t=n.get('type',''); title=(n.get('title') or '').lower(); flat=json.dumps(n.get('widgets_values',''),ensure_ascii=False).lower()
        if 'loadvideo' in t.lower() or t in ('VHS_LoadVideo','LoadVideo'):
            set_load_video(n,frames);counts['video']+=1
        if t=='LoadImage' or ('loadimage' in t.lower() and 'batch' not in t.lower()):
            set_load_image(n);counts['image']+=1
        if 'videocombine' in t.lower() or t in ('SaveVideo','VHS_VideoCombine'):
            set_output(n,prefix);counts['output']+=1
        is_text=('text' in t.lower() or 'prompt' in t.lower() or 'string' in t.lower()) and isinstance(n.get('widgets_values'),(list,dict))
        if is_text:
            neg=('negative' in title or 'negative prompt' in flat or 'worst quality' in flat or 'bad quality' in flat)
            pos=('prompt' in title or 'positive' in title or 'instruction' in title or '@reference' in flat)
            if neg and set_text(n,negative):counts['negative']+=1
            elif pos and set_text(n,positive):counts['positive']+=1
    if counts['video']==0 or counts['output']==0: raise RuntimeError(f"Patch did not find required video/output nodes: {counts}")
    return counts

def select_final_output(obj, preferred_types, prefix):
    """Leave only the best video output active. Other upstream demo/preview outputs are mode=Never.

    KJNodes Set/Get pairs act as a named virtual bus, not a real `links` edge, so a plain
    links-graph ancestor walk cannot see through them -- on workflows that route the final
    result via Set_result/Get_result (e.g. the official Edit Anything graph) every candidate
    output scores 0 and this raises RuntimeError even though a valid output exists. Fixed by
    resolving GetNode -> matching SetNode (by stored variable name) as a pseudo-ancestor edge.
    A composite/labeled QA-comparison output (AddLabel/ImageConcatMulti in its ancestry) is
    deprioritized against a clean single-result output, since both can legitimately clear the
    preferred-type threshold and the comparison strip otherwise wins on raw ancestor count.
    """
    chosen=[]
    preferred=[x.lower() for x in preferred_types]
    composite_hints=('addlabel','imageconcat')
    for g in graph_dicts(obj):
        nd={n.get('id'):n for n in g.get('nodes',[])}
        rev={k:set() for k in nd}
        for l in g.get('links',[]):
            if isinstance(l,list) and len(l)>=4 and l[1] in nd and l[3] in nd:rev[l[3]].add(l[1])
        setters={}
        for n in nd.values():
            if n.get('type')=='SetNode':
                wv=n.get('widgets_values')
                name=wv[0] if isinstance(wv,list) and wv else None
                if name:setters[name]=n.get('id')
        outs=[n for n in nd.values() if ('videocombine' in n.get('type','').lower() or n.get('type') in ('SaveVideo','VHS_VideoCombine'))]
        if not outs:continue
        def ancestors(nid):
            seen=set();stack=[nid]
            while stack:
                x=stack.pop()
                for y in rev.get(x,()):
                    if y not in seen:seen.add(y);stack.append(y)
                node=nd.get(x)
                if node and node.get('type')=='GetNode':
                    wv=node.get('widgets_values')
                    name=wv[0] if isinstance(wv,list) and wv else None
                    setter=setters.get(name)
                    if setter is not None and setter not in seen:seen.add(setter);stack.append(setter)
            return seen
        ranked=[]
        for n in outs:
            anc=ancestors(n.get('id')); types=' '.join(nd[x].get('type','').lower() for x in anc if x in nd)
            score=sum(100 for q in preferred if q in types)+len(anc)
            if 'loadvideo' in types:score+=20
            if 'loadimage' in types:score+=10
            if any(h in types for h in composite_hints):score-=50
            ranked.append((score,n,anc))
        ranked.sort(key=lambda z:z[0],reverse=True)
        best=ranked[0][1]
        if ranked[0][0] < 100:continue
        for _,n,_ in ranked:
            if n is best:
                n['mode']=0;set_output(n,prefix);chosen.append(n.get('id'))
            else:n['mode']=2
    if not chosen:raise RuntimeError(f'Could not identify final output downstream of {preferred_types}')
    return chosen

def patch_ea(base,kind,lora,sidecar,prefix):
    x=copy.deepcopy(base)
    pos='Propagate the altered appearance from @reference across the entire guide video. Preserve the guide video exact camera movement, acceleration, orbit, perspective, parallax, framing, timing and late optical focus pull. Keep the actor completely absent. Preserve the altered wall, leaded window, sconce and photorealistic flame design. Permit natural flame motion only. Do not invent people, objects, geometry, camera movement or focus changes.'
    neg='restored actor, any person, extra people, invented object, changed room geometry, changed camera path, generic pan, wrong acceleration, wrong parallax, wrong focus timing, texture crawl, flicker, temporal drift, late-shot reference decay, blur, low detail'
    c=patch_common(x,81,prefix,pos,neg)
    lora_nodes=module_nodes=sampler_nodes=0
    for g,n in nodes(x):
        t=n.get('type',''); tl=t.lower()
        if 'editanything' in tl and 'sampler' in tl:
            sampler_nodes+=1
            set_input_widget(n,'window_size',80);set_input_widget(n,'overlap',24);set_input_widget(n,'frame_rate',24)
            if kind=='motion': disconnect_input(g,n,['editanything_module','module','ea_module'])
        if 'editanything' in tl and 'moduleloader' in tl:
            module_nodes+=1
            if kind=='motion': bypass(n)
            else:
                w=n.get('widgets_values')
                if isinstance(w,list) and w:w[0]=sidecar
                elif isinstance(w,dict):
                    for k in ('module_name','lora_name','model_name'):
                        if k in w:w[k]=sidecar
        if ('loraloader' in tl or 'lora loader' in tl) and 'module' not in tl:
            # Limit to loaders in Edit Anything workflow groups where possible.
            flat=(t+' '+(n.get('title') or '')+' '+json.dumps(n.get('widgets_values',''))).lower()
            if 'editanything' in flat or 'edit_anything' in flat:
                w=n.get('widgets_values')
                changed=False
                if isinstance(w,list):
                    for idx,v in enumerate(w):
                        if isinstance(v,str) and (v.endswith('.safetensors') or 'edit_anything' in v.lower()):w[idx]=lora;changed=True;break
                elif isinstance(w,dict):
                    for k in ('lora_name','model_name','name'):
                        if k in w:w[k]=lora;changed=True
                if changed:lora_nodes+=1
    types={n.get('type','') for _,n in nodes(x)}
    if not any('EditAnything' in t for t in types): raise RuntimeError('Downloaded workflow lacks Edit Anything node types')
    if lora_nodes==0 or sampler_nodes==0: raise RuntimeError(f'EA patch incomplete lora={lora_nodes} sampler={sampler_nodes}')
    chosen=select_final_output(x,['EditAnything','LoopingSampler'],prefix)
    return x,{'common':c,'lora_nodes':lora_nodes,'module_nodes':module_nodes,'sampler_nodes':sampler_nodes,'active_outputs':chosen}

def patch_flex(base):
    x=copy.deepcopy(base)
    pos='Use the source Orbit and Turn video as the exact motion and optical guide. Propagate the altered first-frame appearance through the shot: the actor remains completely absent; preserve the altered wall, leaded window, sconce and photorealistic flame treatment. Reproduce the source camera path, acceleration, orbit, parallax, framing, timing and late focus pull exactly. Permit only natural flame motion.'
    neg='restored actor, any person, extra people, invented objects, changed room layout, warped wall, warped window, changed sconce, changed camera path, generic pan, incorrect parallax, incorrect focus timing, texture crawl, flicker, temporal drift, reference decay, blur'
    c=patch_common(x,97,'OrbitTurn_Reskin/FlexAM/diagnostic_97f/reskin',pos,neg)
    sampler=visualizer=0
    for g,n in nodes(x):
        t=n.get('type','')
        if t=='FunTextBox':
            is_negative=False
            nd={z.get('id'):z for z in g.get('nodes',[])}
            for outp in n.get('outputs',[]):
                for lid in outp.get('links') or []:
                    for link in g.get('links',[]):
                        if isinstance(link,list) and len(link)>=5 and link[0]==lid:
                            target=nd.get(link[3]);slot=link[4]
                            if target and slot < len(target.get('inputs',[])) and target['inputs'][slot].get('name')=='negative_prompt':is_negative=True
            set_text(n,neg if is_negative else pos)
        if t=='VideoToTrackingVisualizeAll':
            visualizer+=1;set_input_widget(n,'point_size',4);set_input_widget(n,'cos_level',4);set_input_widget(n,'generate_type','motion_transfer');disconnect_input(g,n,['mask_video'])
        if t=='Wan2_2FunV2VSampler_FlexAM':
            sampler+=1
            for k,v in [('video_length',97),('base_resolution',512),('seed',42),('steps',50),('cfg',6.0),('denoise_strength',1.0),('scheduler','Flow'),('shift',5),('boundary',0.9),('enable_teacache',False),('teacache_offload',False),('cfg_skip_ratio',0.0),('generate_type','motion_transfer'),('dilation_pixels',200)]:set_input_widget(n,k,v)
            disconnect_input(g,n,['mask_video'])
        if 'GroundingDino' in t or 'SAM2' in t or t=='MaskToImage': bypass(n)
    if sampler==0 or visualizer==0:raise RuntimeError(f'FlexAM patch incomplete sampler={sampler}, visualizer={visualizer}')
    chosen=select_final_output(x,['Wan2_2FunV2VSampler_FlexAM'],'OrbitTurn_Reskin/FlexAM/diagnostic_97f/reskin')
    return x,{'common':c,'sampler':sampler,'visualizer':visualizer,'active_outputs':chosen}

def patch_ditto(base):
    x=copy.deepcopy(base)
    pos='Remove the actor completely for the entire shot. Replace the actor area with the correct room background while preserving the source camera movement, acceleration, framing, perspective, parallax, timing and late optical focus pull. Keep the wall, leaded window and sconce geometry stable. Match the altered flame/set appearance shown by the provided first-frame design as closely as instruction-only editing permits. Do not add people or objects.'
    neg='person, actor, extra people, invented objects, camera change, geometry drift, wrong focus timing, flicker, texture crawl'
    c=patch_common(x,73,'OrbitTurn_Reskin/Ditto/diagnostic_73f/reskin',pos,neg)
    resize=0
    for g,n in nodes(x):
        t=n.get('type','')
        if t=='ImageResizeKJv2':
            resize+=1
            w=n.get('widgets_values')
            if isinstance(w,list) and len(w)>=2:w[0]=832;w[1]=480
        set_input_widget(n,'num_frames',73);set_input_widget(n,'frame_count',73);set_input_widget(n,'frame_rate',24)
    types={n.get('type','') for _,n in nodes(x)}
    if not any('WanVideo' in t for t in types) or not any('VACE' in t for t in types):raise RuntimeError('Ditto workflow lacks WanVideo/VACE nodes')
    chosen=select_final_output(x,['WanVideoVACEEncode','WanVideoSampler'],'OrbitTurn_Reskin/Ditto/diagnostic_73f/reskin')
    return x,{'common':c,'resize_nodes':resize,'active_outputs':chosen}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='workflows/generated');args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);report={}
    ea,sha=download_json(EA_URL);report['edit_anything_upstream_sha256']=sha
    variants=[
      # NB 2026-08-06: upstream repo has NO "v1.1" motion-transfer file -- v1.1 is a completely
      # different, unrelated track (the no-reference multitask LoRA, prompt-only, no motion
      # transfer at all). The real motion-transfer files are versioned v0.1. Confirmed against
      # the live Alissonerdx/EditAnything HF repo file listing + its README on 2026-08-06.
      ('01_EditAnything_Motion_R256.json','motion','edit_anything_30k_v0.1_motion_transfer_r256.safetensors',None,'OrbitTurn_Reskin/EditAnything_Motion_R256/diagnostic_81f/reskin'),
      ('02_EditAnything_Motion_R128.json','motion','edit_anything_30k_v0.1_motion_transfer_r128.safetensors',None,'OrbitTurn_Reskin/EditAnything_Motion_R128/diagnostic_81f/reskin'),
      ('05_EditAnything_RefV2V_Full.json','ref','edit_anything_reference_v0.1_r128_ref_adaln_proj-role_embedding-ref_attn-ref_visual_proj.standard.safetensors','edit_anything_reference_v0.1_r128_ref_adaln_proj-role_embedding-ref_attn-ref_visual_proj.module.safetensors','OrbitTurn_Reskin/EditAnything_RefV2V_Full/diagnostic_81f/reskin'),
      ('06_EditAnything_RefV2V_Simple.json','ref','edit_anything_reference_v0.1_r128_ref_adaln_proj-role_embedding.standard.safetensors','edit_anything_reference_v0.1_r128_ref_adaln_proj-role_embedding.module.safetensors','OrbitTurn_Reskin/EditAnything_RefV2V_Simple/diagnostic_81f/reskin')]
    for fn,k,l,m,p in variants:
        w,r=patch_ea(ea,k,l,m,p);json.dump(w,open(out/fn,'w'),indent=2,ensure_ascii=False);report[fn]=r
    fw,sha=download_json(FLEX_URL,LOCKS['flexam']);report['flexam_upstream_sha256']=sha
    fw,r=patch_flex(fw);json.dump(fw,open(out/'03_FlexAM_MotionTransfer_97f_OFFICIAL_BASE.json','w'),indent=2,ensure_ascii=False);report['flexam']=r
    dw,sha=download_json(DITTO_URL,LOCKS['ditto']);report['ditto_upstream_sha256']=sha
    dw,r=patch_ditto(dw);json.dump(dw,open(out/'07_Ditto_Official_Comfy_73f.json','w'),indent=2,ensure_ascii=False);report['ditto']=r
    json.dump(report,open(out/'MATERIALIZATION_REPORT.json','w'),indent=2)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
