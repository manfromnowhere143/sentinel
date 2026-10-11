from pathlib import Path
import json,hashlib,shutil,subprocess
from i148a_ops import R,D,P,E
old=D/'proof/block_000';origin=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter148-block000-20261011/gpu_packet.tar.gz')
b=json.loads((old/'gpu_source_packet.json').read_text());raw=origin.read_bytes()
assert hashlib.sha256(raw).hexdigest()==b['packet_sha256'] and len(raw)==b['packet_bytes']
for name,row in b['files'].items():
 if name.startswith('packet/'):
  rel=name.removeprefix('packet/');data=(R/rel).read_bytes()
  assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],name
  assert data==subprocess.check_output(['git','show',b['commit']+':'+rel],cwd=R),name
E.mkdir(exist_ok=False)
(E/'gpu_packet.tar.gz').write_bytes(raw)
(P/'gpu_source_packet.json').write_bytes((old/'gpu_source_packet.json').read_bytes())
print(b['commit'],b['packet_bytes'])
