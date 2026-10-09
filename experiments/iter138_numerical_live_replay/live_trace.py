"""Link the unchanged numerical controller to each applied simulation action."""

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
from threadpoolctl import threadpool_info

from experiments.iter136_hugsim_recoverability_canary import replay_trace as legacy
from experiments.iter137_controller_execution_contract.controller import Controller

CONTROLLER_SHA = '7784c0a885bba33414a680d2f943f3a701d7ba38bf29996908c6a7bd4089dc03'


def check_runtime(pools):
    if not pools or any(p['num_threads'] != 1 for p in pools):
        raise ValueError('effective threadpool bound')


class Recorder(legacy.Recorder):
    def __init__(self, output, driver):
        from experiments.iter137_controller_execution_contract import controller
        if hashlib.sha256(Path(controller.__file__).read_bytes()).hexdigest() != CONTROLLER_SHA:
            raise ValueError('controller source identity')
        identity = json.loads(Path(os.environ['SENTINEL_I138_IDENTITY']).read_text(),
                              object_pairs_hook=legacy._pairs, parse_constant=legacy._bad_constant)
        if hashlib.sha256(Path(driver).read_bytes()).hexdigest() != identity['driver_sha256']:
            raise ValueError('driver identity')
        self.stop_at = None
        # Reuse the validated driving-trace schema; run identity and extra contract are explicit.
        self.rows = [dict(schema=legacy.SCHEMA, identity=identity, arm='reference', stop_at=None)]
        self.path = Path(output)/'iter138_trace.jsonl'
        self.stream = self.path.open('xb')
        self._write(self.rows[0])
        self.pending = None
        self.controller = Controller('numerical')
        pools = threadpool_info()
        check_runtime(pools)
        self.contract = (Path(output)/'controller138.jsonl').open('xb')
        header = dict(schema='sentinel.iter138.controller_trace.v1', identity=identity,
                      controller_sha256=CONTROLLER_SHA, mode='numerical', numpy=np.__version__,
                      python=sys.version, platform=platform.platform(), pid=os.getpid(),
                      affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
                      threadpools=pools)
        self.write_contract(header)
        self.control_count = 0
        self.applied_count = 0
        self.receipt = None

    def write_contract(self, value):
        self.contract.write(legacy.canonical(value)+b'\n')
        self.contract.flush()
        if self.contract.tell() > 64*1024*1024:
            raise ValueError('controller log budget')

    def begin(self, obs, info, index):
        super().begin(obs, info, index)
        self.client_start = time.perf_counter_ns()

    def choose(self, incoming):
        self.roundtrip_ns = time.perf_counter_ns()-self.client_start
        try:
            return super().choose(incoming)
        except Exception as exc:
            self.write_contract(dict(frame=self.pending['frame'], time=self.pending['time'],
                input_failure=dict(status='failed', stop_reason='input_failure', control=None,
                                   error_type=type(exc).__name__, error=str(exc))))
            raise ValueError('invalid planner input before actuation') from exc

    def control(self, plan, info):
        if self.receipt is not None or self.pending is None or self.control_count != self.pending['frame']:
            raise ValueError('controller frame ordering')
        start = time.perf_counter_ns()
        receipt = self.controller.run(plan, info['ego_velo'], info['ego_steer'])
        duration = time.perf_counter_ns()-start
        self.write_contract(dict(frame=self.pending['frame'], time=self.pending['time'],
                                 receipt=receipt, complete_call_ns=duration,
                                 client_roundtrip_ns=self.roundtrip_ns))
        if receipt['status'] != 'completed':
            raise ValueError('controller failed before actuation: '+receipt['error_type'])
        self.receipt = receipt
        self.control_count += 1
        return tuple(receipt['numerical']['control'])

    def end_step(self, action, info, terminated, truncated):
        if self.receipt is None or [action['acc'], action['steer_rate']] != self.receipt['numerical']['control']:
            raise ValueError('applied control linkage')
        super().end_step(action, info, terminated, truncated)
        self.applied_count += 1
        self.receipt = None

    def finish(self):
        if self.receipt is not None or self.control_count != self.applied_count:
            raise ValueError('unapplied controller result')
        super().finish()
        self.write_contract(dict(end='completed', frames=self.control_count))
        self.contract.close()
