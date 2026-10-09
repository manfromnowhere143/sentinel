import json,os,subprocess
root='/opt/sentinel-stack/HUGSIM'
code='from hugsim_env.envs.hug_sim import HUGSimEnv; import torch; print("HUGSIM_CLASS_IMPORTED", torch.__version__, torch.cuda.is_available())'
reports=[]
for label,pythonpath in [('known_bad_client_shim_in_simulator',root+':/opt/sentinel-stack/hugsim-shim'),('correct_simulator_scope',root)]:
 env=os.environ.copy();env['PYTHONPATH']=pythonpath
 p=subprocess.run([root+'/.pixi/envs/default/bin/python','-c',code],cwd=root,env=env,capture_output=True,text=True,timeout=90)
 reports.append(dict(label=label,pythonpath=pythonpath,argv=[root+'/.pixi/envs/default/bin/python','-c',code],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
print(json.dumps(reports,indent=2))
