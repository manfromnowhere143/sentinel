import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter148_recovery_study';P=D/'proof';B=P/'block_000_attempt_002';base='21c51ed3ead8d24da410b4913ac1a734507b7c08';branch='research/iter148-recovery-study'
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','--show-toplevel').decode().strip()==str(R)
assert git('branch','--show-current').decode().strip()=='wip-gen17-ci-hardening'
assert git('rev-parse','master').decode().strip()=='8c118b74c699bf0f139f9bd659192bad06b895f8'
assert git('remote','get-url','origin').decode().strip()=='https://github.com/manfromnowhere143/sentinel.git'
assert git('diff','--cached','--binary')==(P/'initial_index.diff').read_bytes()
initial=json.loads(Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010/initial_wip_hashes.json').read_text())
untouched={k:v for k,v in initial.items() if k not in ('CONTINUITY.md','docs/NEXT_PHASE.md')}
for name,expected in untouched.items():
 p=R/name;assert (digest(p) if p.exists() else None)==expected,name
prior=json.loads((P/'prior_iteration_hashes.json').read_text())
for name,expected in prior.items():assert digest(R/name)==expected,name
old148=json.loads((B/'before_resume_hashes.json').read_text());mutable={'experiments/iter148_recovery_study/'+n for n in ('STATE.json','RESULT.md','DECISION.md','proof/SHA256SUMS')}
for name,expected in old148.items():
 if name not in mutable:assert digest(R/name)==expected,name
older=0
for line in git('ls-tree','-r',base,'--','experiments/').decode().splitlines():
 meta,name=line.split('\t');m=re.match(r'experiments/iter(\d+)_',name)
 if not m or not 136<=int(m[1])<=147:continue
 mode,kind,oid=meta.split();assert kind=='blob' and mode=='100644'
 data=(R/name).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,name;older+=1
assert git('hash-object','README.md').decode().strip()==git('rev-parse',':README.md').decode().strip()
flags=subprocess.check_output(['ls','-leO','README.md'],cwd=R,text=True);assert 'uchg' in flags and 'deny delete' in flags
pattern=r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*'
def strip(s):return re.sub(pattern,'',s,count=1,flags=re.M).rstrip()
for name,before in [('CONTINUITY.md','before_CONTINUITY.md.txt'),('docs/NEXT_PHASE.md','before_NEXT_PHASE.md.txt')]:
 current=(R/name).read_text()
 if name=='CONTINUITY.md':current=current.split('\n\n## Iter148 study admission started on 2026-10-11')[0]
 assert strip(current)==strip((P/before).read_text()),name
for name in ['CONTINUITY.md','docs/NEXT_PHASE.md','README.md']:
 current=git('show',branch+':'+name).decode()
 if name=='CONTINUITY.md':current=current.split('\n\n## Iter148 study admission started on 2026-10-11')[0]
 assert strip(current)==strip(git('show',base+':'+name).decode()),'candidate:'+name
count=0
for line in (P/'SHA256SUMS').read_text().splitlines():
 expected,name=line.split('  ',1);assert digest(P/name)==expected,name;count+=1
binding=json.loads((B/'gpu_source_packet.json').read_text());source_files=0
for name,expected in binding['files'].items():
 if name.startswith('packet/'):
  rel=name.removeprefix('packet/');p=R/rel
  assert p.stat().st_size==expected['bytes'] and digest(p)==expected['sha256'],name
  assert p.read_bytes()==git('show',binding['commit']+':'+rel);source_files+=1
for p in [*D.glob('*.py'),R/'tests/test_iter148_recovery_study.py']:
 assert p.read_bytes()==git('show',binding['commit']+':'+str(p.relative_to(R)))
raw_counts={}
for path in sorted((P/'admissions').glob('pair_*.json')):
 a=json.loads(path.read_text());directory=P/'study_raw'/path.stem;n=0
 for p in directory.rglob('*'):
  if p.is_file():assert p.read_bytes()==git('show',a['raw_commit']+':'+str(p.relative_to(R)));n+=1
 raw_counts[path.stem]=n
allowed={'CONTINUITY.md','README.md','docs/NEXT_PHASE.md','tests/test_iter148_recovery_study.py'}
changed=git('diff','--name-only',base,branch).decode().splitlines()
assert all(n in allowed or n.startswith('experiments/iter148_recovery_study/') for n in changed)
identities=git('log',base+'..'+branch,'--format=%an <%ae>|%cn <%ce>').decode().splitlines()
assert identities and all(x=='Daniel Wahnich <cogitoergosum143@gmail.com>|Daniel Wahnich <cogitoergosum143@gmail.com>' for x in identities)
assert not re.search(r'co-authored-by|generated-by|claude|anthropic',git('log',base+'..'+branch,'--format=%B').decode(),re.I)
links=0
for name in ('RESULT.md','DECISION.md','GPU_BINDING.md','HYPOTHESIS.md'):
 for dest in re.findall(r'\]\(([^)]+)\)',(D/name).read_text()):
  if not dest.startswith(('https:','http:','#')):assert (D/dest).exists(),dest;links+=1
state=json.loads((D/'STATE.json').read_text());closure=json.loads((B/'resource_closure.json').read_text());ready=json.loads((B/'gpu_ready_instance.json').read_text())
assert state['cloud_compute_used'] and state['owned_active_jobs']==0 and not state['automatic_restart']
assert state['provider_current_state']==closure['provider']['status']=='TERMINATED'
assert ready['id']==closure['provider']['id'] and ready['lastStartTimestamp']==closure['provider']['lastStartTimestamp']
assert closure['watchdog']['exit_code']==0 and closure['shutdown_verified']
processes=subprocess.check_output(['ps','-axo','pid,command'],text=True)
assert not any(' /tmp/i148a_watchdog.py' in s or ' /tmp/i148a_supervise.py' in s for s in processes.splitlines())
report=dict(status='supported',candidate_checked=git('rev-parse',branch).decode().strip(),unrelated_initial_wip_preserved=len(untouched),iter147_files_preserved=len(prior),prior_iteration_git_blobs_preserved=older,prior_iter148_nonmutable_files_preserved=len(old148)-len(mutable),root_index_unchanged=True,root_readme_unchanged_and_protected=True,root_and_candidate_docs_only_active_block_and_appended_iter148_entries=True,master_unchanged=True,proof_inventory_entries_verified=count,frozen_packet_repository_files_verified=source_files,tested_scientific_source_unchanged=True,raw_files_equal_before_analysis_commits=raw_counts,new_commit_human_identity_count=len(identities),new_local_links_verified=links,cloud_compute_used=True,exact_owned_start_terminated=True,watchdog_exited=True,automatic_restart=False)
(B/'final_preservation_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
