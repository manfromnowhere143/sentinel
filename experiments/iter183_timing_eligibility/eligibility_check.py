"""Separate eligibility replay and rational corner checks; no producer imports."""

from collections import Counter
import math
import struct

from experiments.iter182_late_frontier_timing.bound_check import check_bound
from experiments.iter182_late_frontier_timing.premature_check import check_completion
from .common import encode, require, sha


class EligibilityReplay:
    def __init__(self, geometry, old, limit):
        self.geometry, self.old, self.limit = geometry, old, limit
        self.namespace = sha(encode({"dynamics": old, "geometry": geometry}))
        self.cache, self.counts, self.last_time = {}, Counter(), 0.0
        route = geometry["route"]
        deadlines = [c["hazard_time"] for c in geometry["comparators"].values()]
        constraints = [c for c in geometry["comparators"].values() if c["hazard_time"] == 8]
        partition = [
            all(
                (j + 1) / (0.9 * len(route)) >= c["rc"] - old["progress_slack"] for c in constraints
            )
            for j in range(len(route))
        ]
        self.applicable = bool(
            deadlines
            and max(deadlines) == 8
            and constraints
            and any(partition)
            and not all(partition)
            and len(route) >= 2
            and all(math.isfinite(z) and -1000 <= z <= 1000 for point in route for z in point)
            and (old["dt"], old["speed_bound"], old["acceleration_bound"]) == (0.25, 6, 2)
        )

    def check(self, row):
        claim = row["eligibility"]
        require(
            set(claim)
            == {"records", "eligible_prefix", "complete", "motion_interrupted", "finish"},
            "eligibility_schema",
        )
        require(
            type(claim["complete"]) is bool
            and type(claim["motion_interrupted"]) is bool
            and type(claim["eligible_prefix"]) is int,
            "eligibility_types",
        )
        records, valid, trace = claim["records"], row["valid_prefix"], row["trace"]
        finish = claim["finish"]
        require(
            type(finish) in (int, float) and math.isfinite(finish) and finish >= self.last_time,
            "eligibility_finish",
        )
        require(
            [r["prefix"] for r in records] == list(range(1, len(records) + 1))
            and len(records) <= valid,
            "eligibility_population",
        )
        if claim["motion_interrupted"]:
            require(
                not records and not claim["complete"] and finish >= self.limit,
                "eligibility_motion_interruption",
            )
        else:
            require(valid == 0 or bool(records), "eligibility_empty_scan")
            if len(records) < valid:
                require(records[-1]["end"] >= self.limit, "eligibility_early_stop")
        ceiling, excluded_seen = valid, False
        checkpoint_witness = valid > 0 and trace[0]["frame"] < 32 <= trace[valid]["frame"]
        for index, record in enumerate(records, 1):
            require(
                set(record)
                == {
                    "prefix",
                    "frame",
                    "status",
                    "key",
                    "hit",
                    "progress",
                    "completion",
                    "excluded",
                    "start",
                    "progress_end",
                    "completion_start",
                    "end",
                },
                "eligibility_record_schema",
            )
            require(
                type(record["hit"]) is bool
                and record["frame"] == trace[index]["frame"]
                and type(record["prefix"]) is int,
                "eligibility_record_identity",
            )
            start, end = record["start"], record["end"]
            require(
                all(type(v) in (int, float) and math.isfinite(v) for v in (start, end))
                and self.last_time <= start <= end <= finish,
                "eligibility_ordered_clock",
            )
            self.last_time = end
            status, state, frame = record["status"], trace[index]["state"], trace[index]["frame"]
            if start >= self.limit:
                expected = "deadline_before"
            elif excluded_seen:
                expected = "inherited_exclusion"
            elif frame < 24 or frame >= 32:
                expected = "outside_window"
            elif not self.applicable:
                expected = "outside_contract"
            elif not (
                len(state) == 5
                and all(type(v) in (int, float) and math.isfinite(v) for v in state)
                and all(abs(z) <= 1000 for z in state[:3])
                and -1e-12 <= state[3] <= 6 + 1e-12
            ):
                expected = "outside_domain"
            else:
                expected = "certificate"
            if expected != "certificate":
                require(
                    status == expected
                    and record["key"] is None
                    and record["hit"] is False
                    and all(
                        record[k] is None
                        for k in ("progress", "completion", "progress_end", "completion_start")
                    ),
                    "eligibility_unchecked",
                )
                outcome = (
                    None if expected == "deadline_before" else expected == "inherited_exclusion"
                )
                require(record["excluded"] is outcome, "eligibility_unchecked_outcome")
            else:
                key = self.namespace + ":" + sha(struct.pack(">5dq", *state, frame))
                require(record["key"] == key, "eligibility_cache_identity")
                if key in self.cache:
                    require(
                        status == "checked"
                        and record["hit"] is True
                        and all(
                            record[k] is None
                            for k in ("progress", "completion", "progress_end", "completion_start")
                        ),
                        "eligibility_cache_hit",
                    )
                    outcome = self.cache[key]
                    self.counts["cache_hits"] += 1
                else:
                    require(
                        record["hit"] is False and status in ("checked", "partial_progress"),
                        "eligibility_cache_miss",
                    )
                    mid = record["progress_end"]
                    require(
                        type(mid) in (int, float) and math.isfinite(mid) and start <= mid <= end,
                        "eligibility_progress_clock",
                    )
                    progress = check_bound(
                        record["progress"], state, frame, self.geometry, self.old, 32
                    )
                    self.counts["progress_certificates"] += 1
                    if status == "partial_progress":
                        require(
                            record["completion"] is None
                            and record["completion_start"] is None
                            and end >= self.limit,
                            "eligibility_partial_progress",
                        )
                        outcome = progress
                    else:
                        second = record["completion_start"]
                        require(
                            type(second) in (int, float)
                            and math.isfinite(second)
                            and mid <= second <= end
                            and second < self.limit,
                            "eligibility_completion_clock",
                        )
                        premature = check_completion(
                            record["completion"], state, frame, self.geometry, self.old, 32
                        )
                        self.counts["completion_certificates"] += 1
                        outcome = progress or premature
                        self.cache[key] = outcome
                require(
                    type(record["excluded"]) is bool and record["excluded"] == outcome,
                    "eligibility_exclusion",
                )
            require(not (checkpoint_witness and outcome is True), "constraint_false_exclusion")
            if outcome and not excluded_seen:
                ceiling, excluded_seen = index - 1, True
                self.counts["first_excluded_prefixes"] += 1
            if end >= self.limit:
                require(
                    index == len(records) and not claim["complete"], "eligibility_deadline_stop"
                )
            self.counts[status] += 1
        require(
            claim["complete"] == (not claim["motion_interrupted"] and finish < self.limit),
            "eligibility_completion_flag",
        )
        if claim["complete"]:
            require(len(records) == valid, "eligibility_missing_prefix")
            require(
                claim["eligible_prefix"] == ceiling and row["interrupted"] is None,
                "eligibility_prefix",
            )
        else:
            require(
                claim["eligible_prefix"] == 0
                and row["interrupted"] == "time_budget"
                and finish >= self.limit,
                "eligibility_interruption",
            )
            self.counts["interrupted_evaluations"] += 1
        self.last_time = finish
        self.counts["evaluations"] += 1

    def summary(self):
        return dict(**dict(sorted(self.counts.items())), distinct_certificate_pairs=len(self.cache))
