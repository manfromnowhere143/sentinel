import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');P=R/'experiments/iter146_route_outcome_contract/proof';base='dd91e417d43c6a4874d0c7c482f6fade9ea4061d';branch='research/iter146-route-outcome-contract'
def git(*argv):return subprocess.check_output(['git',*argv],cwd=R)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
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
# Verify earlier iteration files against parent Git object identities without checkout.
older=0
for line in git('ls-tree','-r',base,'--',*[f'experiments/iter{n}_'+suffix for n,suffix in [(136,'hugsim_recoverability_canary'),(137,'controller_execution_contract'),(138,'numerical_live_replay'),(139,'finite_pulse_recoverability'),(140,'contact_actuation'),(141,'nominal_continuation'),(142,'nominal_continuation_completion'),(143,'model_contract'),(144,'timed_trajectory'),(145,'constrained_execution')]]).decode().splitlines():
 meta,name=line.split('\t');mode,kind,oid=meta.split();assert kind=='blob' and mode=='100644'
 data=(R/name).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert actual==oid,name;older+=1
assert git('hash-object','README.md').decode().strip()==git('rev-parse',':README.md').decode().strip()
flags=subprocess.check_output(['ls','-leO','README.md'],cwd=R,text=True);assert 'uchg' in flags and 'deny delete' in flags
# Root docs may change only the active block and the two appended Iter146 entries.
def strip_active(s):return re.sub(r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*','',s,count=1,flags=re.M).rstrip()
for name,before in [('CONTINUITY.md','before_CONTINUITY.md.txt'),('docs/NEXT_PHASE.md','before_NEXT_PHASE.md.txt')]:
 current=(R/name).read_text()
 if name=='CONTINUITY.md':current=current.split('\n\n## Iter146 full-horizon contract work started on 2026-10-10')[0]
 assert strip_active(current)==strip_active((P/before).read_text()),name
# Each raw packet still equals the commit made before its first aggregate replay.
raw_counts={}
groups=[('cpu_raw','4c36188c813c68aab2f16ebd5b281ea96de02300')]
a=json.loads((P/'gpu_aggregate.json').read_text())
groups += [('gpu_raw/'+arm,commit) for arm,commit in a['raw_commits'].items()]
for folder,commit in groups:
 count=0
 for p in (P/folder).rglob('*'):
  if p.is_file():assert p.read_bytes()==git('show',commit+':'+str(p.relative_to(R)));count+=1
 raw_counts[folder]=count
# Verify retained proof inventory and exact tested correction source.
count=0
for line in (P/'SHA256SUMS').read_text().splitlines():
 expected,name=line.split('  ',1);assert digest(P/name)==expected,name;count+=1
binding=json.loads((P/'corrected_source_test_binding.json').read_text())
for name,expected in binding['files'].items():assert digest(R/name)==expected,name
# Candidate scope and metadata.
allowed={'CONTINUITY.md','README.md','docs/NEXT_PHASE.md','tests/test_iter146_route_outcome_contract.py'}
changed=git('diff','--name-only',base,branch).decode().splitlines()
assert all(n in allowed or n.startswith('experiments/iter146_route_outcome_contract/') for n in changed)
identities=git('log',base+'..'+branch,'--format=%an <%ae>|%cn <%ce>').decode().splitlines()
assert identities and all(x=='Daniel Wahnich <cogitoergosum143@gmail.com>|Daniel Wahnich <cogitoergosum143@gmail.com>' for x in identities),identities
messages=git('log',base+'..'+branch,'--format=%B').decode();assert not re.search(r'co-authored-by|generated-by|claude|anthropic',messages,re.I)
links=0
for name in ('RESULT.md','DECISION.md','TIMING_CORRECTION.md'):
 for dest in re.findall(r'\]\(([^)]+)\)',(P.parent/name).read_text()):
  if not dest.startswith(('https:','http:','#')):assert (P.parent/dest).exists(),dest;links+=1
s=json.loads((P.parent/'STATE.json').read_text());close=json.loads((P/'resource_closure.json').read_text());assert s['provider_state_last_observed']==close['provider']['status']=='TERMINATED' and close['watchdog']['exit_code']==0
assert s['owned_active_jobs']==0 and not s['automatic_restart'] and not s['live_study_admitted']
r=dict(status='supported',candidate_checked=git('rev-parse',branch).decode().strip(),unrelated_initial_wip_preserved=len(untouched),iter145_hashes_preserved=len(prior),prior_iteration_git_blobs_preserved=older,root_index_unchanged=True,root_readme_unchanged_and_protected=True,root_docs_only_active_block_and_appended_iter146_entries=True,master_unchanged=True,raw_files_equal_prior_commits=raw_counts,proof_inventory_entries_verified=count,corrected_test_source_hashes_verified=True,new_commit_human_identity_count=len(identities),new_local_links_verified=links,provider_terminated=True,watchdog_exited=True,automatic_restart=False,live_study_admitted=False)
(P/'final_preservation_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
