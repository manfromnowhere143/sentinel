import json,sys
from pathlib import Path
packet=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010/optimizer_source_v2');sys.path.insert(0,str(packet))
from experiments.iter145_constrained_execution import independent as m
raw=json.loads(Path('/Users/danielwahnich/workspace/sentinel/experiments/iter145_constrained_execution/proof/optimizer_raw_v2.json').read_text())
old=json.loads((packet/'experiments/iter144_timed_trajectory/proof/raw_qualification.json').read_text())
for r in raw['candidate']:
 try:m.certificate(r['result'])
 except Exception:
  print('candidate',r['kind'],r['index'],flush=True);raise
print(m.validate(raw,old))
