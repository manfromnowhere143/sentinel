"""Case-lifetime timing certificates; physical motion and proposal work are unchanged."""

import math
import struct
import time

from experiments.iter182_late_frontier_timing.bound import progress_bound
from experiments.iter182_late_frontier_timing.premature import completion_bound
from .common import encode, require, sha


class Eligibility:
    def __init__(self, geometry, old, started):
        self.geometry, self.old, self.started = geometry, old, started
        self.namespace = sha(encode(dict(geometry=geometry, dynamics=old)))
        self.cache = {}
        times = [c["hazard_time"] * 4 for c in geometry["comparators"].values()]
        route = geometry["route"]
        limits = [
            c["rc"] - old["progress_slack"]
            for c in geometry["comparators"].values()
            if c["hazard_time"] == 8
        ]
        allowed = (
            [(i + 1) / (0.9 * len(route)) >= max(limits) for i in range(len(route))]
            if limits
            else []
        )
        self.contract = bool(
            times
            and max(times) == 32
            and limits
            and any(allowed)
            and not all(allowed)
            and len(route) >= 2
            and all(math.isfinite(v) and abs(v) <= 1000 for p in route for v in p)
            and old["dt"] == 0.25
            and old["speed_bound"] == 6
            and old["acceleration_bound"] == 2
        )

    def elapsed(self):
        return time.monotonic() - self.started

    def inspect(self, row, prefix, inherited, deadline):
        limit = deadline - self.started
        begin = self.elapsed()
        record = dict(
            prefix=prefix,
            frame=row["frame"],
            status=None,
            key=None,
            hit=False,
            progress=None,
            completion=None,
            excluded=None,
            start=begin,
            progress_end=None,
            completion_start=None,
            end=begin,
        )
        if begin >= limit:
            record["status"] = "deadline_before"
            return record
        state, frame = row["state"], row["frame"]
        if inherited:
            record.update(status="inherited_exclusion", excluded=True)
        elif not 24 <= frame < 32:
            record.update(status="outside_window", excluded=False)
        elif not self.contract:
            record.update(status="outside_contract", excluded=False)
        elif not (
            len(state) == 5
            and all(type(v) in (int, float) and math.isfinite(v) for v in state)
            and max(map(abs, state[:3])) <= 1000
            and -1e-12 <= state[3] <= 6 + 1e-12
        ):
            record.update(status="outside_domain", excluded=False)
        else:
            require(type(frame) is int, "eligibility_clock")
            key = self.namespace + ":" + sha(struct.pack(">5dq", *state, frame))
            record["key"] = key
            if key in self.cache:
                p, c = self.cache[key]
                record.update(status="checked", hit=True, excluded=p["excluded"] or c["excluded"])
            else:
                p = progress_bound(state, frame, self.geometry, self.old, 32)
                record.update(progress=p, progress_end=self.elapsed(), excluded=p["excluded"])
                if record["progress_end"] >= limit:
                    record.update(status="partial_progress", end=record["progress_end"])
                    return record
                second = self.elapsed()
                if second >= limit:
                    record.update(status="partial_progress", end=second)
                    return record
                record["completion_start"] = second
                c = completion_bound(state, frame, self.geometry, self.old, 32)
                self.cache[key] = (p, c)
                record.update(
                    status="checked", completion=c, excluded=p["excluded"] or c["excluded"]
                )
        record["end"] = self.elapsed()
        return record

    def scan(self, rows, valid, motion_interrupted, deadline):
        records, usable, cut, expired = [], valid, False, motion_interrupted is not None
        witnessed = valid > 0 and rows[0]["frame"] < 32 <= rows[valid]["frame"]
        if not expired:
            for k in range(1, valid + 1):
                record = self.inspect(rows[k], k, cut, deadline)
                records.append(record)
                require(
                    not (witnessed and record["excluded"] is True), "constraint_false_exclusion"
                )
                if record["end"] >= deadline - self.started:
                    expired = True
                    break
                if record["excluded"] and not cut:
                    usable, cut = k - 1, True
        finished = self.elapsed()
        expired = expired or finished >= deadline - self.started
        return dict(
            records=records,
            eligible_prefix=0 if expired else usable,
            complete=not expired,
            motion_interrupted=motion_interrupted is not None,
            finish=finished,
        )
