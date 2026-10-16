"""Exact conditional adapter and preregistered finite schedule."""

from .common import BASE, read, require


def check_plan(root, plan):
    fixed = dict(
        iteration=184,
        amendment=1,
        audit_retry_producer_seconds=300,
        status="preregistered",
        record_count=15,
        probe_roots=[[83, 8, 7], [98, 8, 6], [110, 2, 1]],
        remaining_attempts=[7385, 5465, 3929],
        seeds=[20261015] * 3,
        original_wall_seconds=12.51213537500007,
        target_frame=32,
        max_actions=96,
        connection_attempt_budget=128,
        audit_producer_seconds=300,
        audit_checker_seconds=900,
        search_producer_seconds=900,
        search_checker_seconds=3600,
        max_output_bytes=268435456,
        max_rss_bytes=1073741824,
        minimum_free_bytes=2147483648,
    )
    require(all(plan.get(k) == v for k, v in fixed.items()), "fixed_contract")
    parent = read(root, "experiments/iter183_timing_eligibility/adapter.py").decode()
    changes = {
        'rng.uniform(start_frame, plan["max_actions"])': 'rng.uniform(0, plan["max_actions"])',
        "0, -math.pi / 3, start_frame]": "0, -math.pi / 3, 0]",
        "from .eligibility import Eligibility": "from experiments.iter183_timing_eligibility.eligibility import Eligibility",
    }
    for before, after in changes.items():
        require(parent.count(before) == 1, "adapter_anchor")
        parent = parent.replace(before, after)
    require(read(root, BASE / "adapter.py") == parent.encode(), "conditional_adapter")
