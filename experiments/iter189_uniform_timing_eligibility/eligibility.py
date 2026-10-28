"""Preserve late constraints; apply the admitted one-step rule to both selectors."""

import math
import struct
import time

from experiments.iter183_timing_eligibility.eligibility import Eligibility as LateEligibility
from experiments.iter188_early_timing_feasibility.bound import certificate
from .common import encode, require, sha


class Eligibility:
    def __init__(self, geometry, old, started):
        self.geometry, self.old, self.started = geometry, old, started
        require(isinstance(geometry["comparators"], dict), "checkpoint_schema")
        times = [c["hazard_time"] for c in geometry["comparators"].values()]
        require(
            all(type(t) in (int, float) and math.isfinite(t) and t >= 0 for t in times),
            "checkpoint_times",
        )
        self.has_checkpoint = bool(times)
        self.legacy = LateEligibility(geometry, old, started)
        self.namespace = sha(
            encode(dict(rule="iter188-one-step-v1", geometry=geometry, dynamics=old))
        )
        self.cache = {}

    def elapsed(self):
        return time.monotonic() - self.started

    def inspect(self, row, prefix, inherited, deadline):
        begin = self.elapsed()
        result = dict(
            prefix=prefix,
            frame=row["frame"],
            status=None,
            key=None,
            hit=False,
            certificate=None,
            excluded=None,
            start=begin,
            end=begin,
        )
        if begin >= deadline - self.started:
            result["status"] = "deadline_before"
            return result
        state, frame = row["state"], row["frame"]
        require(
            isinstance(state, list)
            and len(state) == 5
            and all(type(v) in (int, float) and math.isfinite(v) for v in state),
            "state_domain",
        )
        require(type(frame) is int and 0 <= frame <= 96, "absolute_frame")
        if inherited:
            result.update(status="inherited_exclusion", excluded=True)
        elif not self.has_checkpoint:
            result.update(status="no_checkpoint", excluded=False)
        elif frame >= 32:
            result.update(status="after_checkpoint", excluded=False)
        else:
            key = self.namespace + ":" + sha(struct.pack(">5dq", *state, frame))
            result["key"] = key
            if key in self.cache:
                result.update(status="checked", hit=True, excluded=self.cache[key])
            else:
                bound = certificate(state, frame, self.geometry, self.old)
                self.cache[key] = bound["status"] == "excluded"
                result.update(status="checked", certificate=bound, excluded=self.cache[key])
        result["end"] = self.elapsed()
        return result

    def scan(self, rows, valid, motion_interrupted, deadline):
        legacy = self.legacy.scan(rows, valid, motion_interrupted, deadline)
        records, usable, cut = [], legacy["eligible_prefix"], False
        expired = not legacy["complete"]
        witnessed = valid > 0 and rows[0]["frame"] < 32 <= rows[valid]["frame"]
        if not expired:
            for index in range(1, legacy["eligible_prefix"] + 1):
                record = self.inspect(rows[index], index, cut, deadline)
                records.append(record)
                require(not (witnessed and record["excluded"] is True), "uniform_false_exclusion")
                if record["end"] >= deadline - self.started:
                    expired = True
                    break
                if record["excluded"] and not cut:
                    usable, cut = index - 1, True
        finished = self.elapsed()
        expired = expired or finished >= deadline - self.started
        return dict(
            legacy=legacy,
            records=records,
            eligible_prefix=0 if expired else usable,
            complete=not expired,
            motion_interrupted=motion_interrupted is not None,
            finish=finished,
        )
