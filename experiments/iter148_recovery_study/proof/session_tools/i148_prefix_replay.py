from pathlib import Path
import sys,json
R=Path('/Users/danielwahnich/workspace/sentinel');sys.path.insert(0,str(R))
from experiments.iter146_route_outcome_contract.gpu_check import verify_case
from experiments.iter148_recovery_study.compare import compare
from experiments.iter147_full_horizon_execution.coordinator import record,raw_identity
P=R/'experiments/iter146_route_outcome_contract/proof';arms={}
for arm in ('nominal','monitor','brake_t0','brake_t2_5'):
 old=json.loads((P/(arm+'_pair_analysis.json')).read_text());raw=P/'gpu_raw'/arm
 raw_identity(R,old['raw_commit'],raw)
 arms[arm]=[verify_case(raw/'runs'/f'scene-0013-easy-00__{arm}__{replica}') for replica in (1,2)]
comparisons={arm:compare(arms['nominal'],arms['monitor'],arms[arm]) for arm in ('brake_t0','brake_t2_5')}
result=dict(status='supported',kind='replay_of_existing_iter146_qualification_not_new_study_data',comparisons=comparisons)
record(R/'experiments/iter148_recovery_study/proof/prior_gpu_prefix_replay.json',result);print(json.dumps(result))
