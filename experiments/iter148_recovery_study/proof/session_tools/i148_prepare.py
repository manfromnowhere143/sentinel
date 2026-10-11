from pathlib import Path
import json
R=Path('/Users/danielwahnich/workspace/sentinel');O=R/'experiments/iter147_full_horizon_execution/proof/session_tools';D=R/'experiments/iter148_recovery_study';P=D/'proof';B=P/'block_000';B.mkdir(exist_ok=False)
def save(name,s):
 Path('/tmp/'+name+'.py').write_text(s)
 (P/'session_tools'/(name+'.py')).write_text(s)
def common(s):
 return s.replace('i147g_','i148g_').replace('/datasets/nuscenes-full/hugsim/iter147_gpu_20261010','/datasets/nuscenes-full/hugsim/iter148_study_20261011').replace('sentinel-iter147-gpu-budget','sentinel-iter148-block000-budget')
s=common((O/'i147g_ops.py').read_text()).replace("P=R/'experiments/iter147_full_horizon_execution/proof'; E=pathlib.Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter147-gpu-20261010')", "D=R/'experiments/iter148_recovery_study'; P=D/'proof/block_000'; E=pathlib.Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter148-block000-20261011')")
s=s.replace("actual['id']==ready['id'] and actual['status']=='TERMINATED'", "actual['id']==ready['id'] and actual['lastStartTimestamp']==ready['lastStartTimestamp'] and actual['status']=='TERMINATED'")
s+="\nBRANCH='research/iter148-recovery-study'\nRAW=D/'proof/study_raw'\nADMISSIONS=D/'proof/admissions'\n"
save('i148g_ops',s)
for name in ['preflight','watchdog','postflight','progress']:
 save('i148g_'+name,common((O/f'i147g_{name}.py').read_text()))
s=common((O/'i147g_start.py').read_text()).replace('>=15','>=17');save('i148g_start',s)
s=common((O/'i147g_budget.py').read_text()).replace('iteration=147','iteration=148,block=0').replace('eight fixed qualification slots','eight fixed study slots, first scenario only');save('i148g_budget',s)
s=common((O/'i147g_deploy.py').read_text()).replace('iter147_full_horizon_execution/QUALIFICATION_PLAN.json','iter148_recovery_study/STUDY_PLAN.json').replace('iter147_full_horizon_execution.pair','iter148_recovery_study.pair')
s=s.replace("a.extractall(control)","assert len(a.getmembers())==len(RECORDS) and len({t.name for t in a.getmembers()})==len(a.getmembers())\n assert sum(t.size for t in a.getmembers())<32*1024**2\n a.extractall(control)")
s=s.replace("from experiments.iter145_constrained_execution.resources import file_identity", "from experiments.iter145_constrained_execution.resources import file_identity\nfrom experiments.iter148_recovery_study.admission import basis\nqualification=basis(packet)")
s=s.replace("report=dict(control=str(control)","report=dict(qualification_sha256=qualification,control=str(control)")
save('i148g_deploy',s)
s=common((O/'i147g_collect.py').read_text()).replace('from i148g_ops import P,E,ssh,run,BASE','from i148g_ops import P,E,R,RAW,ssh,run,BASE\nimport shutil\nsys.path.insert(0,str(R))\nfrom experiments.iter148_recovery_study.admission import local_capacity\nlocal_capacity(shutil.disk_usage(R).free)')
s=s.replace("dest=P/'gpu_raw'/arm", "dest=RAW/arm")
s=s.replace("or p.name.startswith('scene-0013-easy-00__'+arm+'__') ", "")
s=s.replace("assert hashlib.sha256(raw).hexdigest()==binding['sha256']", "assert len(raw)==binding['bytes'] and hashlib.sha256(raw).hexdigest()==binding['sha256']")
s=s.replace("  if not p.is_file():continue", "  if not p.is_file():continue")
save('i148g_collect',s)
s=common((O/'i147g_supervise.py').read_text()).replace('from i148g_ops import P,E,stop\nR=P.parents[2]','from i148g_ops import P,E,R,stop')
s=s.replace("'i147_commit'","'i148_commit'").replace('iter147:','iter148:').replace('fixed qualification worker/replay gate','fixed study worker/replay gate')
save('i148g_supervise',s)
s=(O/'i147_price.py').read_text().replace("D=Path('experiments/iter147_full_horizon_execution/proof')", "D=Path('experiments/iter148_recovery_study/proof/block_000')")
save('i148_price',s)
