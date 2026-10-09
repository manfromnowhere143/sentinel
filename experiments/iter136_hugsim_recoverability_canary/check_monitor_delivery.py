"""Check recorded frozen monitor parameters and per-frame trajectory delivery, not safety."""

import argparse
import json
from pathlib import Path

try:
    from .replay_trace import _bad_constant, _pairs, difference, load_trace, plain
except ImportError:
    from replay_trace import _bad_constant, _pairs, difference, load_trace, plain


PARAMS = {'cpa_margin': 1.5, 'dt': 0.5, 'max_gap': 30.0, 'min_closing': 3.0,
          'min_score': 0.3, 'release_k': 4, 'ttc_thresh': 2.5}


def check(rows, decisions):
    plain(decisions)
    frames = rows[1:-1]
    if len(frames) != len(decisions):
        raise ValueError('missing monitor decisions')
    for frame, decision in zip(frames, decisions):
        if 'trace_error' in decision or decision.get('trace_version') != 'iter48_hugsim_union_v1':
            raise ValueError('monitor error or schema')
        if decision.get('params') != PARAMS:
            raise ValueError('monitor parameters')
        if type(decision.get('frame_index')) is not int or (
            decision.get('frame_index') != frame['frame'] or decision.get('ts') != frame['time']
        ):
            raise ValueError('monitor alignment')
        if type(decision.get('brake')) is not bool:
            raise ValueError('missing monitor brake state')
        expected = [[0.0, 0.0]] * 6 if decision['brake'] else decision['traj']
        if difference(frame['incoming_plan'], expected):
            raise ValueError('monitor trajectory delivery')
    return {'status': 'matched', 'frames': len(frames), 'parameters': PARAMS,
            'scope': 'recorded parameters and client-to-simulator trajectory delivery only'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('decisions', type=Path)
    args = parser.parse_args()
    if args.decisions.is_symlink() or args.decisions.stat().st_size > 16 * 1024**2:
        raise ValueError('decision file type or size')
    decisions = [json.loads(row, object_pairs_hook=_pairs, parse_constant=_bad_constant)
                 for row in args.decisions.read_text().splitlines()]
    print(json.dumps(check(load_trace(args.trace), decisions), sort_keys=True, indent=2))
