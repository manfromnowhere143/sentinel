#!/usr/bin/env python3
"""Build the merged analysis log for the power run.

The measurement was interrupted by five machine-freezing incidents (root cause: memory
exhaustion on a swapless image; see RESULT.md) and completed across three run logs. This script
reconstructs a single analyzable log: for every (arm, scenario, sequence) pair it keeps the LAST
block with the highest episode count across the input logs, in canonical pair order. Episodes
are deterministic per run index, so any two blocks of the same pair agree on their common
prefix — verified here (a mismatch aborts the merge).

off/side-0921 is expected at n=19: its run_19 reproducibly froze the host (3 attempts, 2
physical hosts); accepted and documented.

Usage: merge_power14_logs.py <out.log> <in1.log> [<in2.log> ...]
"""
import collections
import re
import sys

OUT, *INS = sys.argv[1:]
MARK = re.compile(r'^##### P14PAIR (\w+) (\w+) (\d+)')
SCORE = re.compile(r'ncap_score: ')

blocks = collections.OrderedDict()  # (arm, scen, seq) -> list of blocks (each: list of lines)
for path in INS:
    cur_key = None
    cur_lines = []
    for line in open(path, errors='replace'):
        m = MARK.search(line)
        if m:
            if cur_key is not None:
                blocks.setdefault(cur_key, []).append(cur_lines)
            cur_key = m.groups()
            cur_lines = [line]
        elif cur_key is not None:
            cur_lines.append(line)
    if cur_key is not None:
        blocks.setdefault(cur_key, []).append(cur_lines)


def scores_of(lines):
    return [ln for ln in lines if SCORE.search(ln)]


chosen = {}
for key, cands in blocks.items():
    best = None
    for b in cands:
        if best is None or len(scores_of(b)) >= len(scores_of(best)):
            best = b  # >= keeps the LAST block on ties
    # determinism cross-check: every candidate's scores must be a prefix of the chosen block's
    bs = [ln.strip() for ln in scores_of(best)]
    for b in cands:
        cs = [ln.strip() for ln in scores_of(b)]
        if bs[:len(cs)] != cs:
            sys.exit(f'MERGE ABORT: non-prefix score mismatch for {key} — determinism violated')
    chosen[key] = best

CLASSES = ['stationary', 'frontal', 'side']
ARMS = ['off', 'best']
with open(OUT, 'w') as f:
    for arm in ARMS:
        for scen in CLASSES:
            for key in sorted(k for k in chosen if k[0] == arm and k[1] == scen):
                f.writelines(chosen[key])

print(f'merged {len(chosen)} pair blocks from {len(INS)} logs -> {OUT}')
for key in sorted(chosen):
    n = len(scores_of(chosen[key]))
    flag = '' if n == 20 or (key == ('off', 'side', '0921') and n == 19) else '  <-- UNEXPECTED COUNT'
    print(f'  {key[0]:5s} {key[1]:10s} {key[2]}  n={n}{flag}')
