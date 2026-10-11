from pathlib import Path
import ast,tempfile,hashlib,json
R=Path.cwd();B=R/'experiments/iter148_recovery_study/proof/block_000_attempt_002'
tree=ast.parse(Path('/tmp/i148a_complete_deployment.py').read_text())
s=next(node.value for node in ast.walk(tree) if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('import io,tarfile'))
checks=[]
for fault in ['none','changed_packet','initialized_pair','runs','map_cache','execution_manifest.json','deployment_continuation_started.json','symlink_packet_file']:
 with tempfile.TemporaryDirectory(prefix='sentinel-i148-deploy-') as tmp:
  c=Path(tmp)/'control';(c/'packet').mkdir(parents=True);p=c/'packet/source.py';p.write_bytes(b'qualified-source')
  records={'packet/source.py':dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())}
  if fault=='changed_packet':p.write_bytes(b'changed')
  elif fault=='initialized_pair':(c/'pair_000_started.json').write_text('{}')
  elif fault=='symlink_packet_file':
   q=c/'source_original';p.rename(q);p.symlink_to(q)
  elif fault!='none':(c/fault).touch()
  code=s.replace("'/datasets/nuscenes-full/hugsim/iter148_study_20261011'",repr(str(c))).replace('RECORDS',repr(records)).replace('COMMIT',repr('a'*40))
  refused=False
  try:exec(compile(code,'<deployment-prefix>','exec'),{})
  except AssertionError:refused=True
  assert refused==(fault!='none'),fault
  if refused:assert not (c/'deployment_continuation_started.json').exists() or fault=='deployment_continuation_started.json'
  checks.append(dict(fault=fault,refused=refused))
r=dict(status='supported',scope='constructed local deployment-prefix fixtures; no new study execution',checks=checks)
(B/'deployment_completion_known_bads.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
