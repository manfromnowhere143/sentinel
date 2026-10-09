import hashlib,json,pathlib,subprocess,os
r={'files':{},'commands':[]}
paths=['/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0411/scene.pth','/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0411/dynamic_d50e28eab7b144b797d29f8f957922e0.pth','/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0411/ground_param.pkl','/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0411/meta_data.json','/datasets/nuscenes-full/hugsim/3DRealCar/2024_07_02_13_41_48/gs.pth','/opt/sentinel-stack/HUGSIM/pixi.lock','/opt/sentinel-stack/HUGSIM/sim/hugsim_env/envs/hug_sim.py']
for s in paths:
 p=pathlib.Path(s)
 if not p.is_file():r['files'][s]={'missing':True};continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 r['files'][s]={'sha256':h.hexdigest(),'bytes':p.stat().st_size}
code='import sys,torch,gsplat,gymnasium,open3d,omegaconf,numpy; import closed_loop; print(sys.version); print(torch.__version__,torch.version.cuda,numpy.__version__,gsplat.__version__,torch.cuda.is_available())'
env=os.environ.copy();env.update(PIXI_HOME='/datasets/nuscenes-full/hugsim-envs/pixi-home',PIXI_CACHE_DIR='/datasets/nuscenes-full/hugsim-envs/pixi-cache',PYTHONPATH='/opt/sentinel-stack/HUGSIM:/opt/sentinel-stack/hugsim-shim')
cmds=[['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python','-c',code],['docker','run','--rm','--name','sentinel-i136-import-check','--entrypoint','python','uniad:latest','-c','import sys,torch;print(sys.version); print(torch.__version__,torch.version.cuda); import importlib.util; print({k: bool(importlib.util.find_spec(k)) for k in ["open3d","mediapy"]})'],['ls','-la','/datasets/nuscenes-full/hugsim/3DRealCar/2024_07_02_13_41_48/postprocess/shadow.pth']]
for a in cmds:
 try:
  p=subprocess.run(a,capture_output=True,text=True,timeout=150,cwd='/opt/sentinel-stack/HUGSIM',env=env);r['commands'].append(dict(argv=a,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 except subprocess.TimeoutExpired:r['commands'].append(dict(argv=a,status='timeout'))
print(json.dumps(r,indent=2))
