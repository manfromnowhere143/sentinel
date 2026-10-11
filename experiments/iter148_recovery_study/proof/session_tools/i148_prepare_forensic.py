from pathlib import Path
import json,time
R=Path.cwd();D=R/'experiments/iter148_recovery_study';P=D/'proof';B=P/'block_000_attempt_002';F=P/'block_000_forensic';F.mkdir(exist_ok=False)
b=json.loads((B/'gpu_budget.json').read_text());v=json.loads((B/'gpu_shutdown_verified.json').read_text());s=json.loads((B/'supervisor_result.json').read_text());price=json.loads((B/'price_binding.json').read_text());elapsed=time.monotonic()-b['start_monotonic']
assert v['status']=='TERMINATED' and s['shutdown_verified'] and elapsed+900<10800
close=dict(status='supported',execution_status='failed',stopping_reason='progress_transport_failed',provider=v,watchdog=dict(session=92679,exit_code=0),supervisor=dict(session=40891,exit_code=1),shutdown_verified=True,elapsed_to_local_closure_monotonic_seconds=elapsed,registered_seconds=10800,conservative_compute_upper_usd=elapsed/3600*3,official_rate_prorated_estimate_usd=elapsed/3600*price['hourly_usd'],cost_scope='Conservative local monotonic elapsed interval, not invoice; excludes existing disk baseline and taxes.',postflight=json.loads((B/'gpu_postflight_integrity_report.json').read_text()),automatic_restart=False)
(B/'resource_closure.json').write_text(json.dumps(close,indent=2)+'\n')
s=json.loads((D/'STATE.json').read_text());s.update(status='invalid',phase='transport_interruption_evidence_recovery',owned_active_jobs=0,provider_current_state='TERMINATED',watchdog_exit_code=0,supervisor_exit_code=1,stopping_reason='read-only IAP progress query failed; frozen supervisor halted schedule',live_study_admitted=False,next_task='Bounded evidence collection from stopped run; no driving retry. Then close evidence and perform requested README/diagram/memory review before another experiment.')
(D/'STATE.json').write_text(json.dumps(s,indent=2)+'\n')
O=P/'session_tools'
s=(O/'i148a_ops.py').read_text().replace('proof/block_000_attempt_002','proof/block_000_forensic').replace('iter148-block000-attempt002-20261011','iter148-forensic-20261011')
Path('/tmp/i148f_ops.py').write_text(s);(O/'i148f_ops.py').write_text(s)
for name in ['start','watchdog','preflight','postflight']:
 s=(O/f'i148a_{name}.py').read_text().replace('i148a_ops','i148f_ops').replace('sentinel-iter148-block000-attempt002-budget','sentinel-iter148-forensic-budget')
 Path('/tmp',f'i148f_{name}.py').write_text(s);(O/f'i148f_{name}.py').write_text(s)
F.joinpath('BINDING.json').write_text(json.dumps(dict(status='preregistered',scope='Read and retain interrupted pair2 evidence; no new or retried study worker',whole_seconds=900,compute_cap_usd=.75,original_block_cap_seconds=10800,prior_envelope_closure_seconds=elapsed,combined_upper_seconds=elapsed+900,remaining_original_block_seconds_after_recovery_cap=10800-elapsed-900,no_packages=True,no_driving=True,source_changed=False,exact_instance_id=v['id'],original_control='/datasets/nuscenes-full/hugsim/iter148_study_20261011'),indent=2)+'\n')
print(json.dumps(dict(primary_closed_seconds=elapsed,forensic_seconds=900,combined_upper_seconds=elapsed+900)))
