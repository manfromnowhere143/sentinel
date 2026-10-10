from pathlib import Path
import json,hashlib,subprocess
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter145_constrained_execution';P=D/'proof'
c=subprocess.check_output(['git','rev-parse','research/iter145-constrained-execution'],cwd=R).decode().strip()
e=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010/simulator_source_v4');e.mkdir(exist_ok=False)
paths=set(json.loads((D/'INPUTS.json').read_text())['files']);paths.update(str(p.relative_to(R)) for p in D.glob('*.py'));paths.add('tests/test_iter145_constrained_execution.py');paths.add(str((D/'INPUTS.json').relative_to(R)));paths.add(str((D/'SOURCE_ADDITIONS.json').relative_to(R)));paths.update(row['path'] for row in json.loads((D/'SOURCE_ADDITIONS.json').read_text()))
paths.add('experiments/iter141_nominal_continuation/client.py');paths.add('experiments/iter141_nominal_continuation/instrument.py');paths.add('experiments/iter139_finite_pulse_recoverability/instrument.py');paths.add('experiments/iter136_hugsim_recoverability_canary/instrument_driver.py');paths.add('experiments/iter143_model_contract/proof/case_inventory.json')
records={}
for name in sorted(paths):
 raw=subprocess.check_output(['git','show',c+':'+name],cwd=R);p=e/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);records[name]=hashlib.sha256(raw).hexdigest()
(P/'simulator_source_packet.json').write_text(json.dumps(dict(commit=c,packet=str(e),files=records),indent=2)+'\n');print(c,str(e),len(paths))
