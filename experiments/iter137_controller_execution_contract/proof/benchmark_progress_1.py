import json
from pathlib import Path
root=Path('/datasets/nuscenes-full/hugsim/iter137_controller_20261009')
p=root/'benchmark/run.json'
print(p.read_text() if p.exists() else 'run manifest pending')
print((root/'launch.stderr').read_text())
