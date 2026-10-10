from pathlib import Path
import json,hashlib,subprocess
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter145_constrained_execution';P=D/'proof'
c=subprocess.check_output(['git','rev-parse','research/iter145-constrained-execution'],cwd=R).decode().strip()
e=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010/optimizer_source');e.mkdir(exist_ok=False)
paths=set(json.loads((D/'INPUTS.json').read_text())['files']);paths.update(str(p.relative_to(R)) for p in D.glob('*.py'));paths.add('tests/test_iter145_constrained_execution.py');paths.add(str((D/'INPUTS.json').relative_to(R)))
records={}
for name in sorted(paths):
 raw=subprocess.check_output(['git','show',c+':'+name],cwd=R);p=e/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);records[name]=hashlib.sha256(raw).hexdigest()
(P/'optimizer_source_packet.json').write_text(json.dumps(dict(commit=c,packet=str(e),files=records),indent=2)+'\n');print(c,str(e),len(paths))
