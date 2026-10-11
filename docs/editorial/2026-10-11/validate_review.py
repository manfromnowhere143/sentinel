from pathlib import Path
import hashlib,json,re,subprocess,stat,struct
R=Path('/Users/danielwahnich/workspace/sentinel');Q=R/'docs/editorial/2026-10-11'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
pre=json.loads((Q/'before.json').read_text())
allowed={'README.md','docs/ARCHITECTURE.md','experiments/verification/README.md','CONTINUITY.md','docs/NEXT_PHASE.md','docs/research/SENTINEL_INFORMATION_AND_RECOVERABILITY_RESEARCH_DIRECTION_2026-10-09.md','experiments/iter148_recovery_study/DECISION.md','experiments/iter148_recovery_study/STATE.json'}
changed=[]
for name,before in pre['tracked_files'].items():
 p=R/name;now=sha(p) if p.is_file() else None
 if now!=before:changed.append(name);assert name in allowed,name
assert sha(R/'.git/index')==pre['index_sha256']
assert git('rev-parse','master').decode().strip()==pre['master']
assert git('branch','--show-current').decode().strip()==pre['root_branch']
assert sha(R/'docs/history/README_through_iter134.snapshot.txt')==pre['tracked_files']['README.md']
assert sha(R/'docs/history/ARCHITECTURE_original_design.snapshot.txt')==pre['tracked_files']['docs/ARCHITECTURE.md']
assert (R/'README.md').stat().st_flags & stat.UF_IMMUTABLE
assert 'deny delete' in subprocess.check_output(['ls','-lOe',str(R/'README.md')],text=True)
# No change to frozen experiment source, protocols, manifests or raw evidence.
scientific=0
for line in git('ls-tree','-r',pre['candidate'],'--','experiments/').decode().splitlines():
 meta,name=line.split('\t')
 if name in allowed:continue
 mode,kind,oid=meta.split();p=R/name
 assert kind=='blob' and p.is_file(),name
 data=p.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,name
 scientific+=1
files=sorted(allowed-{'experiments/iter148_recovery_study/STATE.json'})+[str((Q/'REVIEW.md').relative_to(R))]
links=0;diagrams=[]
def anchors(s):
 out=[]
 for h in re.findall(r'^#{1,6} (.+)$',s,re.M):
  h=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',h);h=re.sub(r'[^\w\s-]','',h.lower()).replace(' ','-');out.append(h)
 return out
for name in files:
 p=R/name;s=p.read_text()
 # Only current editorial links in continuity, whose historical body is intentionally preserved.
 if name in ('CONTINUITY.md','docs/NEXT_PHASE.md'):s=s[:s.index('\n\n',s.index('> **Active'))]
 for target in re.findall(r'\]\(([^)]+)\)',s):
  if target.startswith(('http','mailto:')):continue
  rel,_,anchor=target.partition('#');dest=(p.parent/rel) if rel else p
  assert dest.exists(),(name,target)
  if anchor and dest.suffix=='.md':assert anchor in anchors(dest.read_text()),(name,target,'anchor')
  links+=1
 for i,b in enumerate(re.findall(r'```mermaid\n(.*?)```',s,re.S),1):
  assert len(b)<1100 and ('classDef' not in b or 'color:' in b)
  key=('readme' if name=='README.md' else 'architecture')+f'-{i}'
  assert (Q/'diagrams'/(key+'.mmd')).read_text()==b
  renders=[]
  for theme in ('light','dark'):
   image=Q/'diagrams'/(key+'-'+theme+'.png');data=image.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);renders.append({'theme':theme,'width':w,'height':h,'sha256':sha(image)})
  diagrams.append({'name':key,'characters':len(b),'renders':renders})
results=sorted(R.glob('experiments/*/RESULT.md'));readme=(R/'README.md').read_text()
assert all(str(p.relative_to(R)) in readme for p in results)
metrics=json.loads((R/'experiments/iter148_recovery_study/proof/block_000_attempt_002/metrics.json').read_text())
state=json.loads((R/'experiments/iter148_recovery_study/STATE.json').read_text())
assert metrics['verified_steps']==metrics['verified_controller_calls']==metrics['verified_loop_over_250ms']==368
assert metrics['verified_episodes']==metrics['verified_completions']==4
assert metrics['verified_controller_over_50ms']==6
assert metrics['incomplete_recorded_steps']==88 and metrics['uninitialized_slots']==107
assert metrics['actual_recovery_rate'] is None and metrics['actual_harm_rate'] is None
assert state['editorial_status']=='complete' and state['owned_active_jobs']==0 and not state['automatic_restart']
assert state['provider_current_state']=='TERMINATED' and state['compared_scenarios']==0
for text in ['+0.783','[+0.605, +0.928]','−0.032 [−0.127, +0.065]','+0.3683 [−0.1901, +0.8866]','859 of 1,205','107 uninitialized','no complete four-arm comparison']:
 assert text.lower() in readme.lower(),text
report={'status':'supported','scope':'Editorial content and preservation audit; not a scientific or publication admission','parent_candidate':pre['candidate'],'local_links_and_anchors_checked':links,'all_result_files_linked':len(results),'diagrams':diagrams,'unrelated_tracked_files_preserved':len(pre['tracked_files'])-len(changed),'tracked_editorial_changes':changed,'experimental_files_unchanged':scientific,'root_index_unchanged':True,'root_branch_unchanged':True,'master_unchanged':True,'historical_snapshots_byte_identical':True,'root_readme_protections_restored':True,'scientific_counts_unchanged':True,'cloud_compute_used_for_editorial':False,'next_experiment_started':False,'known_repository_guard_findings_remaining':4}
(Q/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
(Q/'link_and_coverage_check.json').write_text(json.dumps({'local_links_and_anchors_checked':links,'result_files_linked':len(results),'diagram_count':len(diagrams),'findings':[]},indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('diagrams','tracked_editorial_changes')},indent=2))
