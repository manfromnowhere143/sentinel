#!/usr/bin/env python3
"""Docs integrity guard — runs in CI on every push.

Enforces, automatically, the presentation invariants this repository maintains by hand
otherwise:
  1. Every mermaid block stays under the mobile render budget (~1100 chars) and declares
     explicit `color:` in its classDefs (dark-mode legibility).
  2. Every relative markdown link in tracked docs resolves to an existing file.
  3. Story completeness: every experiment that has a RESULT.md is linked from the README —
     a result that exists but is absent from the front page is a broken narrative.

Exits nonzero with a findings list on any violation.
"""
import glob
import os
import re
import subprocess
import sys

from mission_state import load_state, validate_state

fails = []

mission_state = load_state()
for problem in validate_state(mission_state):
    fails.append(f'MISSION_STATE.json: {problem}')

tracked = subprocess.run(['git', 'ls-files', '*.md'], capture_output=True, text=True).stdout.split()

for f in tracked:
    src = open(f, errors='replace').read()
    base = os.path.dirname(f)
    for i, block in enumerate(re.findall(r'```mermaid\n(.*?)```', src, re.S)):
        if len(block) >= 1100:
            fails.append(f'{f}: mermaid block {i} is {len(block)} chars (budget 1100)')
        if 'classDef' in block and 'color:' not in block:
            fails.append(f'{f}: mermaid block {i} has classDef without explicit color:')
    for text, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', src):
        if target.startswith(('http', '#', 'mailto')):
            continue
        p = os.path.normpath(os.path.join(base, target.split('#')[0]))
        if not os.path.exists(p):
            fails.append(f'{f}: broken link -> {target}')

readme = open('README.md', errors='replace').read()
for result in sorted(glob.glob('experiments/*/RESULT.md')):
    d = os.path.dirname(result)
    if d not in readme:
        fails.append(f'README.md: experiment with a RESULT is not referenced -> {d}')

completed = mission_state['current_completed_iteration']
verdict = mission_state['current_verdict']
next_program = mission_state['next_program']
surface_requirements = {
    'README.md': [
        f'current through iteration {completed}',
        verdict,
        mission_state['current_result'],
    ],
    'docs/NEXT_PHASE.md': [
        f'Canonical current decision: iteration {completed} is complete',
        f"Iteration {next_program['iteration']}",
        next_program['name'],
    ],
    'docs/REPORT.md': [
        f'refreshed 2026-07-16 through iteration {completed}',
        verdict,
    ],
    'docs/paper/STATUS.md': [
        mission_state['paper_state']['status'],
        'HUGSIM transfer null',
        'iteration-134 placebo result',
    ],
    'HANDOFF.md': [
        'Canonical mission state (`MISSION_STATE.json`)',
        f"iteration {completed} / {verdict}",
        f"iteration {next_program['iteration']} / {next_program['phase']}",
    ],
}
for path, required in surface_requirements.items():
    if not os.path.exists(path):
        fails.append(f'{path}: required current-state surface is missing')
        continue
    text = open(path, errors='replace').read()
    normalized_text = ' '.join(text.split())
    for phrase in required:
        if ' '.join(phrase.split()) not in normalized_text:
            fails.append(f'{path}: current-state phrase missing -> {phrase}')

surface_forbidden = {
    'README.md': [
        'current through iteration 133',
        'arXiv submission is in moderation/announcement watch',
    ],
    'docs/REPORT.md': [
        'refreshed 2026-07-14 after iterations 122-123',
        'One simulator (NeuroNCAP/NeuRAD)',
    ],
    'docs/paper/MANUSCRIPT.md': ['venue decision: arXiv first'],
    'HANDOFF.md': ['its gate governs the next action'],
}
for path, forbidden in surface_forbidden.items():
    text = open(path, errors='replace').read()
    normalized_text = ' '.join(text.split())
    for phrase in forbidden:
        if ' '.join(phrase.split()) in normalized_text:
            fails.append(f'{path}: forbidden stale phrase present -> {phrase}')

if fails:
    print('DOCS GUARD FAILED:')
    for x in fails:
        print(' -', x)
    sys.exit(1)
print(f'docs guard: {len(tracked)} markdown files clean; all RESULT experiments surfaced in README')
