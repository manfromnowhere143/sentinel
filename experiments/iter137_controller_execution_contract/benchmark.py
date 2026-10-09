"""Frozen CPU-only benchmark. Exclusive output directory prevents measured retries."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SCHEDULE = [('numerical', 'idle'), ('timed', 'idle'), ('timed', 'contended'),
            ('numerical', 'contended'), ('numerical', 'contended'), ('timed', 'contended'),
            ('timed', 'idle'), ('numerical', 'idle')]
THREADS = {k: '1' for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                           'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS')}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def worker(args):
    os.sched_setaffinity(0, {args.cpu})
    from threadpoolctl import threadpool_info
    import numpy as np
    from controller import Controller, load_corpus

    pools = threadpool_info()
    if not pools or any(p['num_threads'] != 1 for p in pools):
        raise ValueError('effective threadpool constraint')
    controller = Controller(SCHEDULE[args.block][0])
    meta = dict(pid=os.getpid(), affinity=sorted(os.sched_getaffinity(0)), numpy=np.__version__,
                python=sys.version, platform=platform.platform(), threadpools=pools,
                thread_env={k: os.environ.get(k) for k in THREADS}, ambient_load=os.getloadavg(),
                status='running', calls=0)
    meta['library_sha256'] = {p['filepath']: hashlib.sha256(Path(p['filepath']).read_bytes()).hexdigest() for p in pools}
    meta_path = args.output / f'block_{args.block}.meta.json'
    write(meta_path, meta)
    with (args.output / f'block_{args.block}.jsonl').open('x') as output:
        for case in load_corpus():
            row = controller.run(np.array(case['plan'], dtype=case['dtype']), case['velocity'], case['steering'])
            row.update(block=args.block, case_id=case['id'], load=SCHEDULE[args.block][1])
            output.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
            output.flush()
            meta['calls'] += 1
            if row['status'] != 'completed':
                meta['status'] = 'failed'
                write(meta_path, meta)
                return 1
    meta.update(status='completed', ambient_load_after=os.getloadavg())
    write(meta_path, meta)
    return 0


def contend(cpu):
    os.sched_setaffinity(0, {cpu})
    print(json.dumps(dict(pid=os.getpid(), affinity=sorted(os.sched_getaffinity(0)))), flush=True)
    x = 1
    while True:
        x = (x * 1664525 + 1013904223) & 0xffffffff


def run(args):
    if args.output.exists():
        raise ValueError('output exists: measured retries forbidden')
    if args.instance_deadline - time.time() < 1800:
        raise ValueError('less than 30 minutes of instance budget remains')
    args.output.mkdir(parents=True)
    cpu = min(os.sched_getaffinity(0))
    manifest = dict(schema='sentinel.iter137.benchmark.v1', status='running', cpu=cpu,
                    started_utc=datetime.now(timezone.utc).isoformat(),
                    instance_deadline=args.instance_deadline, parent_affinity=sorted(os.sched_getaffinity(0)),
                    hostname=platform.node(), blocks=[], no_driving_episodes=True,
                    python_executable=sys.executable,
                    code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(ROOT.glob('*.py'))})
    start = time.monotonic()
    try:
        for index, (mode, load) in enumerate(SCHEDULE):
            if time.monotonic() - start >= 1800 or time.time() >= args.instance_deadline:
                raise TimeoutError('benchmark/instance ceiling')
            competitors = []
            record = dict(block=index, mode=mode, load=load, competitors=[], returncode=None)
            manifest['blocks'].append(record)
            try:
                if load == 'contended':
                    for _ in range(3):
                        proc = subprocess.Popen([sys.executable, str(Path(__file__)), 'contend', '--cpu', str(cpu)],
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        competitors.append(proc)
                        if not select.select([proc.stdout], [], [], 10)[0]:
                            raise TimeoutError('competitor readiness')
                        record['competitors'].append(json.loads(proc.stdout.readline()))
                    if any(p.poll() is not None for p in competitors):
                        raise RuntimeError('competitor exited before block')
                command = [sys.executable, str(Path(__file__)), 'worker', '--output', str(args.output),
                           '--block', str(index), '--cpu', str(cpu)]
                record['command'] = command
                record['started_utc'] = datetime.now(timezone.utc).isoformat()
                with (args.output / f'block_{index}.stdout').open('x') as out, (args.output / f'block_{index}.stderr').open('x') as err:
                    result = subprocess.run(command, stdout=out, stderr=err, env={**os.environ, **THREADS},
                                            timeout=min(180, 1800-(time.monotonic()-start), args.instance_deadline-time.time()))
                record['returncode'] = result.returncode
                record['competitors_alive_after'] = sum(p.poll() is None for p in competitors)
                record['ended_utc'] = datetime.now(timezone.utc).isoformat()
                if result.returncode != 0 or record['competitors_alive_after'] != len(competitors):
                    raise RuntimeError('failed block or load worker')
            finally:
                for proc in competitors:
                    if proc.poll() is None:
                        proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                record['competitors_reaped'] = [p.returncode for p in competitors]
                write(args.output / 'run.json', manifest)
        manifest['status'] = 'completed'
    except Exception as exc:
        manifest.update(status='failed', error_type=type(exc).__name__, error=str(exc),
                        remaining_calls='unobserved')
    manifest['elapsed_seconds'] = time.monotonic()-start
    manifest['ended_utc'] = datetime.now(timezone.utc).isoformat()
    write(args.output / 'run.json', manifest)
    return 0 if manifest['status'] == 'completed' else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'worker', 'contend'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--cpu', type=int)
    parser.add_argument('--block', type=int)
    parser.add_argument('--instance-deadline', type=float)
    args = parser.parse_args()
    if args.action == 'worker':
        return worker(args)
    if args.action == 'contend':
        return contend(args.cpu)
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
