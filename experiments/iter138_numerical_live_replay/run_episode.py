"""Execute one registered fresh numerical-reference episode on the inspected host; never retry an episode."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time


CONTROL = Path('/datasets/nuscenes-full/hugsim/iter138_control_20261009')
OUTPUT = Path('/datasets/nuscenes-full/hugsim/outputs/iter138-20261009')
HUGSIM = Path('/opt/sentinel-stack/HUGSIM')
ARMS = {'reference_a': 'reference', 'reference_b': 'reference'}
CONTAINER = 'sentinel-i138-client'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_files(files):
    for name, expected in files.items():
        path = Path(name)
        if not path.is_file() or path.is_symlink() or digest(path) != expected:
            raise ValueError(f'runtime file mismatch: {name}')


def check_budget(free_gib, remaining_seconds, output_exists):
    if free_gib < 100 or free_gib - 8 < 25:
        raise ValueError('storage budget')
    if remaining_seconds < 1230:
        raise ValueError('insufficient session runtime for bounded episode and cleanup')
    if output_exists:
        raise ValueError('episode already attempted; no overwrite or retry')


def command(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed: {result.stderr[:2000]}')
    return result.stdout.strip()


def check_runtime_identity(actual_image, expected_image, containers, gpu_processes):
    if actual_image != expected_image:
        raise ValueError('client image identity')
    if containers:
        raise ValueError('another container is running')
    if gpu_processes:
        raise ValueError('GPU process already running')


def predecessors(arm, root):
    if arm == 'reference_a':
        return
    previous = root / 'reference_a'
    receipt = previous / 'episode.json'
    if not receipt.is_file() or json.loads(receipt.read_text()).get('returncode') != 0:
        raise ValueError('previous episode incomplete or failed')
    env = {**os.environ, 'PYTHONPATH': str(CONTROL / 'packet'),
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    result = subprocess.run([str(HUGSIM / '.pixi/envs/default/bin/python'), '-m',
        'experiments.iter138_numerical_live_replay.verify_live',
        str(previous / 'scene-0411_hard_00')], capture_output=True, text=True, env=env, timeout=180)
    with (previous / 'validation_before_b.json').open('x') as output:
        json.dump(dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr), output)
    if result.returncode or json.loads(result.stdout).get('status') != 'validated':
        raise ValueError('previous reference failed independent validation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arm', choices=ARMS)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    if socket.gethostname().split('.')[0] != 'sentinel-gpu':
        raise ValueError('host mismatch')
    manifest_path = CONTROL / 'runtime_manifest.json'
    if digest(manifest_path) != args.manifest_sha256:
        raise ValueError('manifest identity')
    manifest = json.loads(manifest_path.read_text())
    with (CONTROL / 'episode.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_files(manifest['files'])
        check_runtime_identity(
            command(['docker', 'image', 'inspect', manifest['image_id'], '--format', '{{.Id}}']),
            manifest['image_id'], command(['docker', 'ps', '-q']),
            command(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader']))
        run = OUTPUT / args.arm
        check_budget(shutil.disk_usage(OUTPUT.parent).free / 2**30,
                     manifest['deadline_epoch'] - time.time(), run.exists())
        predecessors(args.arm, OUTPUT)
        run.mkdir(parents=True, exist_ok=False)
        environment = os.environ.copy()
        environment.update(
            PYTHONPATH=f'{CONTROL}:{CONTROL}/packet:{HUGSIM}',
            OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
            SENTINEL_ENABLED='1', SENTINEL_I138_ARM=args.arm,
            SENTINEL_I138_IDENTITY=str(CONTROL / 'identity.json'),
            SENTINEL_I138_STOP_AT=ARMS[args.arm],
        )
        # Gym loads this module lazily. Importing closed_loop alone misses this boundary.
        probe = subprocess.run(
            [str(HUGSIM / '.pixi/envs/default/bin/python'), '-c',
             'from hugsim_env.envs.hug_sim import HUGSimEnv; import closed_loop'],
            cwd=HUGSIM, env=environment, capture_output=True, text=True, timeout=90)
        (run / 'environment_import.json').write_text(json.dumps(
            dict(returncode=probe.returncode, stdout=probe.stdout, stderr=probe.stderr),
            indent=2) + '\n')
        if probe.returncode:
            raise RuntimeError('environment class import failed before episode launch')
        check_budget(shutil.disk_usage(OUTPUT.parent).free / 2**30,
                     manifest['deadline_epoch'] - time.time(), False)
        argv = [str(HUGSIM / '.pixi/envs/default/bin/python'), '-u',
                str(CONTROL / 'iter138_closed_loop.py'),
                '--scenario_path', manifest['scenario'],
                '--base_path', str(CONTROL / 'nuscenes_base.yaml'),
                '--camera_path', 'configs/sim/nuscenes_camera.yaml',
                '--kinematic_path', 'configs/sim/kinematic.yaml',
                '--ad', 'uniad', '--ad_cuda', '0', '--i138-output-base', str(run)]
        receipt = dict(arm=args.arm, manifest_sha256=args.manifest_sha256, argv=argv,
                       started_at_utc=datetime.now(timezone.utc).isoformat(),
                       status='running', timeout_seconds=1200)
        (run / 'started.json').write_text(json.dumps(receipt, indent=2) + '\n')
        began = time.monotonic()
        with (run / 'driver.log').open('xb') as log:
            process = subprocess.Popen(argv, cwd=HUGSIM, env=environment,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            receipt['driver_pid'] = process.pid
            try:
                receipt['returncode'] = process.wait(timeout=1200)
                receipt['status'] = 'process_completed'
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                receipt.update(returncode=124, status='timeout')
            finally:
                # Never remove a historical or unrelated container.
                inspect = subprocess.run(
                    ['docker', 'inspect', CONTAINER, '--format',
                     '{{index .Config.Labels "sentinel.iter138.arm"}}'],
                    capture_output=True, text=True, timeout=30)
                if inspect.returncode == 0:
                    if inspect.stdout.strip() != args.arm:
                        receipt['cleanup'] = 'ownership_mismatch_no_removal'
                    else:
                        result = subprocess.run(['docker', 'rm', '-f', CONTAINER],
                                                capture_output=True, text=True, timeout=30)
                        receipt['cleanup'] = dict(returncode=result.returncode,
                                                  stdout=result.stdout, stderr=result.stderr)
                else:
                    receipt['cleanup'] = 'container_absent'
        receipt['elapsed_seconds'] = time.monotonic() - began
        receipt['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        receipt['artifacts'] = {
            str(p.relative_to(run)): {'sha256': digest(p), 'bytes': p.stat().st_size}
            for p in sorted(run.rglob('*')) if p.is_file() and not p.is_symlink()
        }
        (run / 'episode.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))
        return receipt['returncode']


if __name__ == '__main__':
    raise SystemExit(main())
