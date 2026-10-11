from pathlib import Path
import json,sys,time,shutil
R=Path.cwd();sys.path.insert(0,str(R));D=R/'experiments/iter148_recovery_study';P=D/'proof';B=P/'block_000';E=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter148-block000-20261011')
from experiments.iter148_recovery_study.aggregate import summarize
from experiments.iter147_full_horizon_execution.coordinator import record
plan=json.loads((D/'STUDY_PLAN.json').read_text())
record(P/'study_accounting.json',summarize(plan,[]))
closed=json.loads((B/'launch_not_started.json').read_text())
closed.update(status='supported',closure='unused_envelope_closed',launch_status='blocked',watchdog_session=59776,watchdog_exit_code=143,watchdog_exit_scope='Local SIGTERM intentionally cancelled unused watchdog after read-only credential failure; no VM cleanup was asserted.',supervisor_started=False,local_free_bytes=shutil.disk_usage(R).free,study_pairs_initialized=0)
record(B/'resource_closure.json',closed);record(E/'closure.json',closed)
s=json.loads((D/'STATE.json').read_text());s.update(status='blocked',phase='provider_reauthentication_required_before_start',cloud_compute_used=False,owned_active_jobs=0,live_study_admitted=False,admission_scope='Local study implementation and source freeze; fresh provider/runtime gates not observed',automatic_restart=False,study_outcomes_observed=0,study_pairs_initialized=0,study_slots_admitted=0,study_slots_missing=112,provider_current_state='UNOBSERVED',last_verified_provider_state='TERMINATED at Iter147 closure',start_command_issued=False,watchdog_exit_code=143,watchdog_exit_reason='Intentionally stopped unused local guard after credential failure.',source_commit='dd45ad39b26602ad81626ca55332e7ce6d308e91',next_task='After Google Cloud reauthentication, create a fresh first-block envelope and perform provider/resource/runtime admission. Execute only fixed slots 0–7 initially; do not reuse closed attempt paths or retry initialized work.')
(D/'STATE.json').write_text(json.dumps(s,indent=2)+'\n')
