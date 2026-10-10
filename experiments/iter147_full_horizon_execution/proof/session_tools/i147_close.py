from pathlib import Path
import datetime,json,time,shutil
R=Path.cwd();D=R/'experiments/iter147_full_horizon_execution';P=D/'proof';E=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter147-gpu-20261010')
b=json.loads((P/'gpu_budget.json').read_text());provider=json.loads((P/'gpu_shutdown_verified.json').read_text());post=json.loads((P/'gpu_postflight_integrity_report.json').read_text());supervisor=json.loads((P/'supervisor_result.json').read_text());price=json.loads((P/'price_binding.json').read_text())
assert provider['status']=='TERMINATED' and post['status']=='supported' and supervisor['status']=='supported' and supervisor['shutdown_verified']
elapsed=time.monotonic()-b['start_monotonic'];assert elapsed<10800
closure=dict(status='supported',provider=provider,watchdog=dict(session=54396,exit_code=0,output='watchdog cancelled after verified cleanup'),supervisor=dict(session=64333,exit_code=0),postflight=post,elapsed_to_local_closure_monotonic_seconds=elapsed,registered_seconds=10800,conservative_compute_upper_usd=elapsed/3600*3,official_rate_prorated_estimate_usd=elapsed/3600*price['hourly_usd'],pricing_url=price['url'],cost_scope='Conservative elapsed interval includes pre-start preparation, execution, transfers, verification, shutdown and local closure overhead. Estimates are not invoices; existing disk baseline and taxes are excluded. No subtraction across provider/host/local absolute clocks.',automatic_restart=False)
(P/'resource_closure.json').write_text(json.dumps(closure,indent=2)+'\n');(E/'closure.json').write_text(json.dumps(closure,indent=2)+'\n')
a=json.loads((P/'gpu_aggregate.json').read_text());m=json.loads((P/'qualification_metrics.json').read_text())
state=json.loads((D/'STATE.json').read_text());state.update(status='supported',phase='bounded_gpu_qualification_closed',cloud_compute_used=True,owned_active_jobs=0,automatic_restart=False,provider_state_last_observed='TERMINATED',gpu_steps=912,gpu_cases=8,gpu_replica_pairs=4,monitor_injected_actions=802,natural_nominal_actions=110,natural_nominal_collision_cases=6,censored_cases=2,qualified_completion_cases=0,controller_over_50ms=4,full_loop_over_250ms=912,live_study_admitted=False,raw_commits=a['raw_commits'],next_task='Implement study-specific admission and resource/lifecycle binding for the unchanged 112 slots; do not treat qualification as a recovery comparison.')
state['owned_instance']=provider
(D/'STATE.json').write_text(json.dumps(state,indent=2)+'\n')
for n in ('i147_metrics.py','i147_close.py'):shutil.copyfile(Path('/tmp')/n,P/'session_tools'/n)
print(json.dumps(closure,indent=2))
