import sys
sys.path.insert(0,'/Users/danielwahnich/workspace/sentinel')
from pathlib import Path
import hashlib, json, re, subprocess
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter145_constrained_execution';P=D/'proof';E=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
checks={};initial=json.loads((E/'initial_wip_hashes.json').read_text())
for n,h in initial.items():
 if n in ['CONTINUITY.md','docs/NEXT_PHASE.md']:continue
 p=R/n;assert (sha(p) if p.exists() else None)==h,n
checks['unrelated_initial_dirty_paths_preserved']=18
assert git('diff','--cached','--binary')==(E/'initial_index.diff').read_bytes();checks['root_index_preserved']=True
assert git('rev-parse','--abbrev-ref','HEAD').decode().strip()=='wip-gen17-ci-hardening';checks['root_branch_preserved']=True
assert git('rev-parse','master').decode().strip()=='8c118b74c699bf0f139f9bd659192bad06b895f8';checks['master_preserved']=True
assert not git('diff','--','README.md');assert (R/'README.md').stat().st_flags & 2;checks['root_readme_unchanged_immutable']=True
for n in ['CONTINUITY.md','docs/NEXT_PHASE.md']:
 before=(Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-gpu-20261010')/('closure_before_'+Path(n).name)).read_text();after=(R/n).read_text()
 strip=lambda t:re.sub(r'> \*\*Active operator-directed candidate work, 2026-10-10:.*?(?=\n\n)','',t,count=1,flags=re.S)
 if n=='CONTINUITY.md':after=after.split('\n\n## Iter145 resumed GPU qualification on 2026-10-10')[0]
 assert strip(before)==strip(after),n
checks['active_docs_only_expected_edits']=True
count=0
for line in (P/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);assert sha(P/n)==h,n;count+=1
checks['proof_hashes_verified']=count
for n,h in [('optimizer_raw_v3.json','dbb5beebd30387347781babf7deb4e0f6836561276438d6c67e4b61e9930964e'),('integration_raw.json','6a36166422e47aa21ceff041fe82b3f6fabc85c3edc610cc63b1eee1d8f140bd')]:assert sha(P/n)==h,n
checks['measured_raw_hashes_unchanged']=True
packet=E/'simulator_source_v4';files=[p for p in packet.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and '.ruff_cache' not in p.parts]
for p in files:
 rel=str(p.relative_to(packet));assert p.read_bytes()==git('show','8b8fa4239f95482d8419a0d5afc09b18248feb43:'+rel),rel
checks['isolated_source_files_match_measured_commit']=len(files)
for doc in [D/'RESULT.md',D/'DECISION.md']:
 for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
  if not link.startswith(('https:','http:','#')):assert (doc.parent/link.split('#')[0]).exists(),link
checks['new_doc_links_resolve']=True
commits=git('rev-list','958e9da1ee48029279a9c92d215d7c6d09aeabb6..research/iter145-constrained-execution').decode().splitlines()
for c in commits:
 identity=git('show','-s','--format=%an <%ae>%n%cn <%ce>',c).decode().splitlines();assert identity==['Daniel Wahnich <cogitoergosum143@gmail.com>']*2
 message=git('show','-s','--format=%B',c).decode();assert not re.search(r'co-authored|generated.by|claude|anthropic',message,re.I)
checks['human_commit_identity_and_no_model_trailers']=len(commits)
stop=json.loads((P/'gpu_shutdown_verified.json').read_text());assert stop['status']=='TERMINATED' and stop['id']=='3834622546652649531'
assert Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-gpu-20261010/cleanup_verified.json').exists();assert json.loads((D/'STATE.json').read_text())['phase']=='bounded_gpu_qualification_complete'
checks['owned_cloud_stopped_and_milestone_retained']=True
running=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
jobs=[l for l in running.splitlines() if re.search(r'\bpython(?:3(?:\.\d+)?)?\s+/tmp/i145(?:g|r)?_(watchdog|start|preflight|deploy_inventory|asset_diagnose|stop)\.py(?:\s|$)',l)]
assert not jobs,jobs;checks['owned_inspection_processes_exited']=True
raw_root=P/'gpu_raw'
for p in raw_root.rglob('*'):
 if p.is_file():assert p.read_bytes()==git('show','7e5976bb9ee4c54dc5f114ca4392d9f16c202510:'+str(p.relative_to(R))),str(p)
checks['all_gpu_raw_bytes_preserved_since_preanalysis_commit']=True
from experiments.iter145_constrained_execution.analyze_gpu import analyze
assert analyze(raw_root)==json.loads((P/'gpu_aggregate_analysis.json').read_text())
checks['aggregate_reproduces_from_raw']=True
report=dict(status='passed',validated_candidate=git('rev-parse','research/iter145-constrained-execution').decode().strip(),checks=checks)
(P/'resumed_preservation_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
