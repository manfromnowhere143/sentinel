"""Separate composed-policy replay: prior late checks and exact corner proofs."""

from collections import Counter
import math
import struct

from experiments.iter183_timing_eligibility.eligibility_check import EligibilityReplay as LateReplay
from experiments.iter188_early_timing_feasibility.bound_check import verify
from .common import encode, require, sha


class EligibilityReplay:
    def __init__(self, geometry, old, limit):
        self.geometry, self.old, self.limit = geometry, old, limit
        self.legacy = LateReplay(geometry, old, limit)
        self.namespace = sha(
            encode({"dynamics": old, "geometry": geometry, "rule": "iter188-one-step-v1"})
        )
        self.last_time, self.cache, self.counts, self.seconds = 0.0, {}, Counter(), 0.0

    def check(self, row):
        claim = row["eligibility"]
        require(
            set(claim)
            == {"legacy", "records", "eligible_prefix", "complete", "motion_interrupted", "finish"},
            "uniform_schema",
        )
        require(
            type(claim["eligible_prefix"]) is int
            and type(claim["complete"]) is bool
            and type(claim["motion_interrupted"]) is bool,
            "uniform_types",
        )
        legacy = claim["legacy"]
        self.legacy.last_time = self.last_time
        self.legacy.check(
            dict(row, eligibility=legacy, interrupted=None if legacy["complete"] else "time_budget")
        )
        self.last_time = legacy["finish"]
        finish = claim["finish"]
        require(
            type(finish) in (int, float) and math.isfinite(finish) and finish >= self.last_time,
            "uniform_finish",
        )
        require(
            claim["motion_interrupted"] == legacy["motion_interrupted"],
            "uniform_interruption_origin",
        )
        records, ceiling = claim["records"], legacy["eligible_prefix"]
        require(
            isinstance(records, list)
            and [r["prefix"] for r in records] == list(range(1, len(records) + 1))
            and len(records) <= ceiling,
            "uniform_population",
        )
        if not legacy["complete"]:
            require(not records, "uniform_after_late_expiry")
        elif len(records) < ceiling:
            require(bool(records) and records[-1]["end"] >= self.limit, "uniform_early_stop")
        cut = False
        witness = (
            row["valid_prefix"] > 0
            and row["trace"][0]["frame"] < 32 <= row["trace"][row["valid_prefix"]]["frame"]
        )
        for index, record in enumerate(records, 1):
            require(
                set(record)
                == {
                    "prefix",
                    "frame",
                    "status",
                    "key",
                    "hit",
                    "certificate",
                    "excluded",
                    "start",
                    "end",
                },
                "uniform_record_schema",
            )
            state, frame = row["trace"][index]["state"], row["trace"][index]["frame"]
            require(
                type(record["prefix"]) is int
                and type(record["frame"]) is int
                and record["frame"] == frame
                and type(record["hit"]) is bool,
                "uniform_identity",
            )
            start, end = record["start"], record["end"]
            require(
                all(type(t) in (int, float) and math.isfinite(t) for t in (start, end))
                and self.last_time <= start <= end <= finish,
                "uniform_clock",
            )
            self.seconds += end - start
            self.last_time = end
            if start >= self.limit:
                expected, outcome = "deadline_before", None
            else:
                require(
                    isinstance(state, list)
                    and len(state) == 5
                    and all(type(x) in (int, float) and math.isfinite(x) for x in state),
                    "uniform_state",
                )
                require(type(frame) is int and 0 <= frame <= 96, "uniform_frame")
                if cut:
                    expected, outcome = "inherited_exclusion", True
                elif not self.geometry["comparators"]:
                    expected, outcome = "no_checkpoint", False
                elif frame >= 32:
                    expected, outcome = "after_checkpoint", False
                else:
                    expected, outcome = "checked", None
            require(record["status"] == expected, "uniform_status")
            if expected == "checked":
                key = self.namespace + ":" + sha(struct.pack(">5dq", *state, frame))
                require(record["key"] == key, "uniform_cache_identity")
                if key in self.cache:
                    require(
                        record["hit"] is True and record["certificate"] is None, "uniform_cache_hit"
                    )
                    outcome = self.cache[key]
                    self.counts["cache_hits"] += 1
                else:
                    require(
                        record["hit"] is False and isinstance(record["certificate"], dict),
                        "uniform_cache_miss",
                    )
                    outcome = verify(record["certificate"], state, frame, self.geometry, self.old)
                    self.cache[key] = outcome
                    self.counts["certificates"] += 1
            else:
                require(
                    record["key"] is None
                    and record["hit"] is False
                    and record["certificate"] is None,
                    "uniform_unchecked",
                )
            require(record["excluded"] is outcome, "uniform_exclusion")
            require(not (witness and outcome is True), "uniform_success_excluded")
            if outcome and not cut:
                ceiling, cut = index - 1, True
                self.counts["first_excluded_prefixes"] += 1
                if frame < 24:
                    self.counts["early_first_excluded_prefixes"] += 1
            if end >= self.limit:
                require(index == len(records) and not claim["complete"], "uniform_deadline_stop")
            self.counts[expected] += 1
        complete = legacy["complete"] and finish < self.limit
        require(claim["complete"] is complete, "uniform_completion")
        if complete:
            require(
                len(records) == legacy["eligible_prefix"]
                and claim["eligible_prefix"] == ceiling
                and row["interrupted"] is None,
                "uniform_prefix",
            )
        else:
            require(
                claim["eligible_prefix"] == 0
                and row["interrupted"] == "time_budget"
                and finish >= self.limit,
                "uniform_expiry",
            )
        self.last_time = finish
        self.counts["evaluations"] += 1

    def summary(self):
        return dict(
            legacy=self.legacy.summary(),
            uniform=dict(sorted(self.counts.items())),
            distinct_uniform_states=len(self.cache),
            uniform_record_seconds=self.seconds,
        )
