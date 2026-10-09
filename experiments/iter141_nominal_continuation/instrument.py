"""Generate source-bound driver and client; historical files remain untouched."""

import hashlib
from experiments.iter139_finite_pulse_recoverability.instrument import instrument as prior

CLIENT_SHA = "23cce8a2a559b60dc3de394ba890a28adc13b5b24d222936478dad6f83f9aea3"


def instrument(raw):
    data = prior(raw).decode().replace("i139", "i141")
    compile(data, "iter141_closed_loop.py", "exec")
    return data.encode()


def instrument_client(raw):
    if hashlib.sha256(raw).hexdigest() != CLIENT_SHA:
        raise ValueError("upstream client identity")
    data = raw.decode()
    before = (
        "            plan_traj = _sentinel_i48_intervene(plan_traj, results[0], data, args.output)"
    )
    if data.count(before) != 1:
        raise ValueError("client anchor")
    data = data.replace(
        before,
        "            from sentinel141_client import deliver\n"
        "            plan_traj = deliver(plan_traj, results[0], data, args.output,\n"
        "                                _sentinel_i48_intervene, _S48_ENABLED)",
    )
    compile(data, "e2e141.py", "exec")
    return data.encode()
