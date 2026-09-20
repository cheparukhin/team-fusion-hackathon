#!/usr/bin/env python3
"""Plain source-colored cartoons for fixed, sequence-verified engine outputs."""
import argparse,json
from pathlib import Path
from pymol import cmd
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[2]
x=json.loads((a.root/'model_index.json').read_text())
for m in x['models']:
 if m['status']!='verified':continue
 path=repo/m['model_path'];out=path.parent/'cartoon.png'
 cmd.reinitialize();cmd.load(str(path),'candidate');cmd.hide('everything');cmd.show('cartoon','candidate');cmd.set_color('parent_a',[0,0,1]);cmd.set_color('novel_tail',[210/255,45/255,39/255]);cmd.color('parent_a','resi 1-73');cmd.color('novel_tail','resi 74-118');cmd.set('cartoon_loop_radius',.22);cmd.set('cartoon_fancy_helices',1);cmd.set('cartoon_fancy_sheets',1);cmd.set('ray_opaque_background',0);cmd.set('ray_shadows',0);cmd.set('orthoscopic',1);cmd.set('antialias',2);cmd.bg_color('white');cmd.viewport(1800,1600);cmd.orient();cmd.turn('y',15);cmd.zoom('candidate',buffer=6,complete=1);cmd.png(str(out),width=1800,height=1600,dpi=300,ray=1)
 print(out)
