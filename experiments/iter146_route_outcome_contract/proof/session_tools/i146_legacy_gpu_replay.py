import json,sys
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');sys.path.insert(0,str(R))
from experiments.iter146_route_outcome_contract.gpu_check import verify_case
from experiments.iter146_route_outcome_contract.compare import replicas
P=R/'experiments/iter146_route_outcome_contract/proof';count=0
for arm in ('nominal','monitor','brake_t0','brake_t2_5'):
 original=json.loads((P/(arm+'_pair_analysis.json')).read_text())
 pair=[verify_case(P/'gpu_raw'/arm/'runs'/f'scene-0013-easy-00__{arm}__{i}') for i in (1,2)]
 replicas(pair)
 for report,before in zip(pair,original['cases']):
  assert {k:v for k,v in report.items() if k not in ('scientific','route')}==before
  count+=report['steps']
print(json.dumps(dict(status='supported',legacy_gpu_steps=count,legacy_replica_pairs=4,report_fields_unchanged=True,scope='Local replay compatibility of frozen v1 GPU raw with new checker; no new GPU execution.')))
