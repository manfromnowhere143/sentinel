import hashlib,json,pathlib,subprocess
root=pathlib.Path('/opt/sentinel-stack')
files=['UniAD_SIM/tools/e2e.sh','UniAD_SIM/tools/closeloop/e2e.py','HUGSIM/sim/utils/launch_ad.py','HUGSIM/configs/sim/nuscenes_base.yaml','HUGSIM/configs/sim/nuscenes_camera.yaml','HUGSIM/configs/sim/kinematic.yaml','HUGSIM/pixi.toml','HUGSIM/sim/utils/score_calculator.py']
out={'files':{},'commands':[]}
for rel in files:
 p=root/rel
 if p.is_file():
  b=p.read_bytes();out['files'][str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'text':b.decode(),'bytes':len(b)}
 else: out['files'][str(p)]={'missing':True}
for path in ['/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0411/cfg.yaml','/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes/scene-0411-hard-00.yaml']:
 p=pathlib.Path(path);b=p.read_bytes();out['files'][path]={'sha256':hashlib.sha256(b).hexdigest(),'text':b.decode(),'bytes':len(b)}
for argv in [['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.Image}} {{.Status}}'],['docker','image','inspect','uniad:latest','--format','{{.Id}}'],['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used','--format=csv'],['git','-C',str(root/'HUGSIM'),'status','--short'],['git','-C',str(root/'UniAD_SIM'),'status','--short'],['readlink','-f',str(root/'HUGSIM/.pixi')],['ls','-la','/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0411'],['ls','-la','/datasets/nuscenes-full/hugsim-envs/pixi-home/bin'],['df','-h','/','/datasets/nuscenes-full']]:
 p=subprocess.run(argv,capture_output=True,text=True,timeout=30);out['commands'].append(dict(argv=argv,returncode=p.returncode,stdout=p.stdout[:50000],stderr=p.stderr[:50000]))
print(json.dumps(out,indent=2))
