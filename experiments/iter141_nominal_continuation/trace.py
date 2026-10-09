"""Iter141 header contract; reuse frozen structural and state checks from Iter139."""

from copy import deepcopy
from experiments.iter139_finite_pulse_recoverability import trace as prior
from experiments.iter139_finite_pulse_recoverability.trace import (  # noqa: F401
    canonical,
    plain,
    _pairs,
    _bad_constant,
    state,
    observation_hash,
    difference,
)

SCHEMA = "sentinel.iter141.trace.v1"
ARMS = {a: (None, None) for a in ("reference_a", "reference_b", "nominal_a", "nominal_b")}


def normalized(rows):
    value = deepcopy(rows)
    if (
        value[0].get("schema") != SCHEMA
        or value[0].get("arm") not in ("reference", "nominal")
        or value[0].get("onset") is not None
        or value[0].get("duration") is not None
    ):
        raise ValueError("Iter141 header")
    value[0].update(schema=prior.SCHEMA, arm="reference")
    return value


def validate(rows):
    prior.validate(normalized(rows))


def pulse_active(header, timestamp):
    return False


class Recorder(prior.Recorder):
    def finish(self):
        last = self.rows[-1]
        reason = (
            "collision"
            if last["collision"]
            else "route_complete"
            if last["terminated"] and last["route_completion"] >= 1
            else "other_termination"
            if last["terminated"]
            else "truncated"
        )
        footer = dict(end="completed", frames=len(self.rows) - 1, reason=reason)
        validate(self.rows + [footer])
        self._write(footer)
        self.stream.close()
