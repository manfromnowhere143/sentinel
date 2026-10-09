"""Portable descriptive cross-tabulation of already retained benchmark receipts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    rows = [json.loads(line) for i in range(8)
            for line in (ROOT / f'proof/benchmark/block_{i}.jsonl').read_text().splitlines()]
    controls = {}
    for row in rows:
        if row['mode'] == 'timed':
            controls.setdefault(row['case_id'], set()).add(tuple(row['numerical']['control']))
    groups = sorted({r['mode'] + '/' + r['load'] for r in rows})
    result = dict(timed_final_control_variable_cases=sum(len(x) > 1 for x in controls.values()),
                  timed_cases=len(controls),
                  converged_adapter_misses={k: sum(r['numerical']['stop_reason'] == 'converged'
                    and r['timing']['adapter_miss'] for r in rows if r['mode']+'/'+r['load'] == k)
                    for k in groups})
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
