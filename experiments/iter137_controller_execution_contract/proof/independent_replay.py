import json
import os
from pathlib import Path
import subprocess
root=Path('/datasets/nuscenes-full/hugsim/iter137_controller_20261009')
code=root/'packet/experiments/iter137_controller_execution_contract'
cmd=['taskset','-c','0','/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python',str(code/'verify.py'),str(root/'benchmark')]
env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
r=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=600)
(root/'independent_replay.stdout').write_text(r.stdout)
(root/'independent_replay.stderr').write_text(r.stderr)
print(json.dumps(dict(command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),indent=2))
assert r.returncode==0
