#!/usr/bin/env python3
"""Assemble the dynamic operator-handoff snapshot (HANDOFF.md content to stdout).

CONTINUITY.md carries the invariants; this generates the live state automatically from the
repository and (if reachable) the GPU box, so a handoff is one command:

    python3 scripts/make_handoff.py > HANDOFF.md
"""
import glob
import os
import subprocess


def sh(cmd, timeout=90):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except Exception as e:
        return f'(unavailable: {e})'


print('# HANDOFF — dynamic state snapshot\n')
print(f"Generated: {sh('date -u')} by scripts/make_handoff.py. Read CONTINUITY.md first.\n")

print('## Repository state\n```')
print(sh('git log --oneline -8'))
print('```')
dirty = sh('git status --short')
print(f'Working tree: {"CLEAN" if not dirty else "DIRTY — resolve before handoff:" + chr(10) + dirty}\n')

print('## Experiments (status inferred from files)\n')
for d in sorted(glob.glob('experiments/*/')):
    h = os.path.exists(d + 'HYPOTHESIS.md')
    r = os.path.exists(d + 'RESULT.md')
    status = 'RESULT PUBLISHED' if r else ('PRE-REGISTERED, result pending' if h else 'artifacts only')
    print(f'- {d[:-1]}: {status}')

print('\n## GPU box quick-state (live probe)\n```')
probe = sh(
    'timeout 60 gcloud compute ssh sentinel-gpu --zone us-west1-a --tunnel-through-iap '
    '--quiet --command "hostname; uptime; sudo docker ps --format \'{{.Names}}\t{{.Status}}\' | head -6; '
    'ls -t /var/log/sentinel-*.log | head -3; df -h / | tail -1; free -h | tail -1" 2>/dev/null',
    timeout=70)
print(probe if probe else 'BOX UNREACHABLE (auth lapsed? box down?) — ask Daniel: ! gcloud auth login')
print('```')
print('If any docker container named renderer/model/ncap (or a random-name ncap) is up, a run')
print('is IN FLIGHT — identify it from the newest /var/log/sentinel-*.log and DO NOT relaunch.\n')

print('## Open threads (from the newest experiment docs)')
latest = sorted(glob.glob('experiments/*/HYPOTHESIS.md'), key=os.path.getmtime)[-1]
print(f'- Newest pre-registration: {latest} — read it in full; its gate governs the next action.')
for f in ('docs/NEXT_PHASE.md', 'docs/paper/MANUSCRIPT.md'):
    if os.path.exists(f):
        print(f'- {f}: check its status ledger/decision rules.')
print('\n## Verification before you act')
print('- Run: ruff check . && pytest -q && python3 scripts/validate_docs.py')
print('- All three must pass before and after your changes; CI enforces the same on push.')
