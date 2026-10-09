"""Build the new driver from source-bound Iter136 instrumentation, retaining seed 136."""

from experiments.iter136_hugsim_recoverability_canary.instrument_driver import instrument as old


def instrument(raw):
    source = old(raw).decode()
    substitutions = [
        ("from replay_trace import Recorder", "from live_trace import Recorder"),
        ("--i136-output-base", "--i139-output-base"),
        ("args.i136_output_base", "args.i139_output_base"),
        (
            "acc, steer_rate = traj2control(plan_traj, info)",
            "acc, steer_rate = trace.control(plan_traj, info)",
        ),
    ]
    for before, after in substitutions:
        if source.count(before) != 1:
            raise ValueError("driver anchor")
        source = source.replace(before, after)
    compile(source, "iter139_closed_loop.py", "exec")
    return source.encode()
