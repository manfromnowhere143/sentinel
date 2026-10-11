import tempfile,tarfile,subprocess,os,json
from pathlib import Path
from i148g_ops import E,P,R
with tempfile.TemporaryDirectory(prefix='sentinel-i148-packet-') as t:
 with tarfile.open(E/'gpu_packet.tar.gz','r:gz') as a:a.extractall(t,filter='data')
 root=Path(t)/'packet';env=os.environ.copy();env.update(PYTHONPATH=str(root),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 code="from pathlib import Path;import json;from experiments.iter148_recovery_study.admission import basis,validate_plan;from experiments.iter147_full_horizon_execution.protocol import validate;r=Path.cwd();p=json.loads((r/'experiments/iter148_recovery_study/STUDY_PLAN.json').read_text());validate_plan(r,p);validate(r,p);print(basis(r));print(len(p['slots']))"
 q=subprocess.run(['python3','-c',code],cwd=root,env=env,capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout)
 q=subprocess.run(['python3','-m','experiments.iter148_recovery_study.pair','--help'],cwd=root,env=env,capture_output=True,text=True);assert q.returncode==0,q.stderr;print(q.stdout)
print('Exact frozen packet imports and study qualification binding passed')
