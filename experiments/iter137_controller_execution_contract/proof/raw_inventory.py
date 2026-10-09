import hashlib
import json
from pathlib import Path
root=Path('/datasets/nuscenes-full/hugsim/iter137_controller_20261009')
run=json.loads((root/'benchmark/run.json').read_text())
assert run['status']=='completed'
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'benchmark').iterdir()) if p.is_file()}
print(json.dumps(dict(files=files,deployment=json.loads((root/'deployment.json').read_text()),launch=json.loads((root/'launch.json').read_text())),indent=2))
