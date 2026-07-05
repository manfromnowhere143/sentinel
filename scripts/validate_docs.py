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

fails = []

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

if fails:
    print('DOCS GUARD FAILED:')
    for x in fails:
        print(' -', x)
    sys.exit(1)
print(f'docs guard: {len(tracked)} markdown files clean; all RESULT experiments surfaced in README')
