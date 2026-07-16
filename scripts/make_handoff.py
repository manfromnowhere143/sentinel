#!/usr/bin/env python3
"""Assemble the dynamic operator-handoff snapshot (HANDOFF.md content to stdout).

CONTINUITY.md carries the invariants; this generates the live state automatically from the
repository and (if reachable) the GPU box, so a handoff is one command:

    python3 scripts/make_handoff.py > HANDOFF.md
"""
import glob
import os
import subprocess

from mission_state import current_summary, load_state, validate_state


def sh(cmd, timeout=90):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except Exception as e:
        return f'(unavailable: {e})'


print('# HANDOFF — dynamic state snapshot\n')
print(f"Generated: {sh('LC_ALL=C date -u')} by scripts/make_handoff.py. Read CONTINUITY.md first.\n")

mission_state = load_state()
state_problems = validate_state(mission_state)
if state_problems:
    raise SystemExit('MISSION_STATE.json invalid:\n - ' + '\n - '.join(state_problems))

print('## Repository state\n```')
print(sh('git log --oneline -8'))
print('```')
dirty = '\n'.join(
    line for line in sh('git status --short').splitlines()
    if line.strip() and not line.endswith('HANDOFF.md')
)
print(f'Working tree: {"CLEAN" if not dirty else "DIRTY — resolve before handoff:" + chr(10) + dirty}\n')

next_program = mission_state['next_program']
print('## Canonical mission state (`MISSION_STATE.json`)\n')
print(f"- Current: {current_summary(mission_state)}")
print(f"- Current result: {mission_state['current_result']}")
print(f"- Next program: {next_program['name']}")
print('- Authorized now:')
for action in next_program['authorized_actions']:
    print(f'  - {action}')
print('- Forbidden now:')
for action in next_program['forbidden_actions']:
    print(f'  - {action}')
print()

print('## Experiments (status inferred from files)\n')
for d in sorted(glob.glob('experiments/*/')):
    h = os.path.exists(d + 'HYPOTHESIS.md')
    r = os.path.exists(d + 'RESULT.md')
    status = 'RESULT PUBLISHED' if r else ('PRE-REGISTERED, result pending' if h else 'artifacts only')
    print(f'- {d[:-1]}: {status}')

print('\n## GPU box quick-state (live probe)\n```')
gpu_probe_cmd = (
    'timeout 60 gcloud compute ssh sentinel-gpu --zone us-west1-a --tunnel-through-iap '
    '--quiet --command "hostname; uptime; '
    "sudo docker ps --format '{{.Names}}\t{{.Status}}' > /tmp/sentinel_handoff_docker_ps.txt; "
    'if [ -s /tmp/sentinel_handoff_docker_ps.txt ]; then '
    'echo GPU_RUN_STATE=IN_FLIGHT_CONTAINERS; head -6 /tmp/sentinel_handoff_docker_ps.txt; '
    'else echo GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS; fi; '
    'rm -f /tmp/sentinel_handoff_docker_ps.txt; '
    'ls -t /var/log/sentinel-*.log | head -3; df -h / | tail -1; free -h | tail -1" '
    '2>/dev/null'
)
probe = (
    'GPU_RUN_STATE=NOT_PROBED_OFFLINE_GENERATION'
    if os.environ.get('SENTINEL_HANDOFF_SKIP_LIVE_PROBE') == '1'
    else sh(gpu_probe_cmd, timeout=70)
)
print(probe if probe else 'BOX UNREACHABLE (auth lapsed? box down?) — ask Daniel: ! gcloud auth login')
print('```')
print('If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run')
print('is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.\n')

print('## Open threads (from the newest experiment docs)')
print(f"- Canonical completed experiment: {mission_state['current_result']} — read it before opening new work.")
pending = sorted(
    h for h in glob.glob('experiments/*/HYPOTHESIS.md')
    if not os.path.exists(h.replace('HYPOTHESIS.md', 'RESULT.md'))
)
deprecated = set(mission_state.get('deprecated_pending_hypotheses', []))
active_hypothesis = mission_state.get('active_hypothesis')
if active_hypothesis:
    print(f'- Active pending pre-registration: {active_hypothesis} — read it with MISSION_STATE.json; neither file overrides the other.')
for legacy in sorted(deprecated.intersection(pending)):
    print(f'- Deprecated pending pre-registration: {legacy} — historical only; it does not govern the next action.')
print(f"- Canonical next action: iteration {next_program['iteration']} / {next_program['phase']} / {next_program['name']}.")
for f in ('docs/NEXT_PHASE.md', 'docs/paper/MANUSCRIPT.md'):
    if os.path.exists(f):
        print(f'- {f}: check its status ledger/decision rules.')
print('\n## Verification before you act')
print('- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py')
print('- All three must pass before and after your changes; CI enforces the same on push.')
