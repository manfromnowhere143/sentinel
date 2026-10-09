import json
from pathlib import Path
root=Path('/datasets/nuscenes-full/hugsim/iter137_controller_20261009')
report=json.loads((root/'benchmark/run.json').read_text())
print(json.dumps(dict(status=report['status'],blocks=len(report['blocks']),returncodes=[b['returncode'] for b in report['blocks']],elapsed_seconds=report.get('elapsed_seconds')),indent=2))
print((root/'launch.stderr').read_text())
