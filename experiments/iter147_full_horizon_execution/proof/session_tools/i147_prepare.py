from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel'); O=R/'experiments/iter146_route_outcome_contract/proof/session_tools'; D=R/'experiments/iter147_full_horizon_execution'; P=D/'proof'
def convert(s):
 return s.replace('i146g','i147g').replace('iter146_route_outcome_contract','iter147_full_horizon_execution').replace('iter146-gpu','iter147-gpu').replace('iter146_gpu','iter147_gpu').replace('iter146-gpu-budget','iter147-gpu-budget').replace('e2e146','e2e147')
s=convert((O/'i146g_packet.py').read_text()).replace("research/iter146-route-outcome-contract","research/iter147-full-horizon-execution")
s=s.replace(";assert c=='9f78e514000f94ab069e846a7b6796009702a223'",'')
s=s.replace('for d in (old,D):',"for d in (old,R/'experiments/iter146_route_outcome_contract',D):")
s=s.replace("paths.add('experiments/iter145_constrained_execution/ACTOR_FILES.json')","paths.add('experiments/iter145_constrained_execution/ACTOR_FILES.json')\npaths.add('experiments/iter147_full_horizon_execution/QUALIFICATION_PLAN.json')")
Path('/tmp/i147g_packet.py').write_text(s)
s=convert((O/'i146g_deploy.py').read_text()).replace('iter147_full_horizon_execution.gpu_pair','iter147_full_horizon_execution.pair')
s=s.replace("for n in ['e2e147.py'", "(control/'plan.json').write_bytes((packet/'experiments/iter147_full_horizon_execution/QUALIFICATION_PLAN.json').read_bytes())\nfor n in ['plan.json','e2e147.py'")
s=s.replace("cases=['scene-0013-easy-00.yaml']", "cases=sorted(set(s['scenario'] for s in json.loads((control/'plan.json').read_text())['slots']))")
Path('/tmp/i147g_deploy.py').write_text(s)
s=convert((O/'price.py').read_text());Path('/tmp/i147_price.py').write_text(s)
s=convert((O/'i146g_progress.py').read_text()).replace("c.glob('*_pair.json')","c.glob('pair_*_result.json')")
s=s.replace("v['client_tail']", "v['parent_tail']=(p/'parent.log').read_text()[-600:] if (p/'parent.log').exists() else None\n v['client_tail']")
Path('/tmp/i147g_progress.py').write_text(s)
s=convert((O/'i146g_launch_pair.py').read_text())
s=s.replace("arm=sys.argv[1];assert arm in ('nominal','monitor','brake_t0','brake_t2_5')", "pair=int(sys.argv[1]);assert 0<=pair<4\narm=f'pair_{pair:03d}'\nfrom pathlib import Path\nsys.path.insert(0,str(P.parents[2]))\nfrom experiments.iter147_full_horizon_execution.protocol import identity\nplan=json.loads((P.parent/'QUALIFICATION_PLAN.json').read_text())")
s=s.replace('remaining>1300','remaining>2600')
a=s.index("permit=dict(");b=s.index('encoded=json.dumps',a)
s=s[:a]+'''permit=dict(pair=pair,plan_sha256=identity(plan),manifest_sha256=dep['manifest_sha256'],status='supported',previous=None)
if pair:
 path=P/f'pair_{pair-1:03d}_analysis.json';previous=json.loads(path.read_text());assert previous['status']=='supported'
 commit=__import__('subprocess').check_output(['git','rev-parse','research/iter147-full-horizon-execution'],cwd=P.parents[2],text=True).strip()
 assert path.read_bytes()==__import__('subprocess').check_output(['git','show',commit+':'+str(path.relative_to(P.parents[2]))],cwd=P.parents[2])
 permit['previous']=previous
''' + s[b:]
s=s.replace('iter147_full_horizon_execution.gpu_pair','iter147_full_horizon_execution.pair').replace("'--arm',ARM", "'--pair',str(PAIR)")
s=s.replace(".replace('ARM',repr(arm))", ".replace('ARM',repr(arm)).replace('PAIR',str(pair))")
Path('/tmp/i147g_launch_pair.py').write_text(s)
s=convert((O/'i146g_collect.py').read_text());a=s.index('arm=sys.argv');b=s.index("s='''",a)
s=s[:a]+"pair=int(sys.argv[1]);assert 0<=pair<4\narm=f'pair_{pair:03d}';attempt=''\n"+s[b:]
s=s.replace("arm+'_pair.json'", "arm+'_result.json'")
s=s.replace("for folder in sorted((c/'runs').glob('*__'+arm+'__*')):","plan=json.loads((c/'plan.json').read_text())\nfor slot in plan['slots'][PAIR*2:PAIR*2+2]:\n folder=c/'runs'/slot['id']\n if not folder.exists():continue")
s=s.replace("'deployment_report.json','e2e147.py'", "'deployment_report.json','plan.json','e2e147.py'")
s=s.replace('<100*1024**2','<512*1024**2',1).replace("binding['bytes']<100*1024**2", "binding['bytes']<256*1024**2").replace('t.size<=100*1024**2','t.size<=256*1024**2')
s=s.replace(".replace('ARM',repr(arm))", ".replace('ARM',repr(arm)).replace('PAIR',str(pair))")
s=s.replace(" for t in a.getmembers():", " assert sum(t.size for t in a.getmembers())<512*1024**2\n assert len({t.name for t in a.getmembers()})==len(a.getmembers())\n for t in a.getmembers():")
Path('/tmp/i147g_collect.py').write_text(s)
