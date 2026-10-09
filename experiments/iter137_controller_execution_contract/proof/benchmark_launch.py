import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
root=Path('/datasets/nuscenes-full/hugsim/iter137_controller_20261009')
manifest=json.loads((root/'deployment.json').read_text())
for name,expected in manifest['files'].items():
 assert hashlib.sha256((root/'packet'/name).read_bytes()).hexdigest()==expected
assert json.loads((root/'source_parity.stdout').read_text())['status']=='passed'
assert not (root/'benchmark').exists()
assert 1791554138.290096-time.time()>1800
cmd=['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python',str(root/'packet/experiments/iter137_controller_execution_contract/benchmark.py'),'run','--output',str(root/'benchmark'),'--instance-deadline',str(1791554138.290096)]
with (root/'launch.stdout').open('x') as out,(root/'launch.stderr').open('x') as err:
 proc=subprocess.Popen(cmd,stdout=out,stderr=err,start_new_session=True)
record=dict(pid=proc.pid,command=cmd,host_utc=time.time(),source_commit=manifest['source_commit'])
(root/'launch.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
