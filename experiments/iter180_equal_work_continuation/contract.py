"""Fixed paired population, work ceilings and candidate width."""

from .common import require

PARENT = "d71eab91dbe7d0979d1e3f6d7259e0a84d1bc89b"
ARMS = ["program", "beam"]
FIXED = dict(
    iteration=180,
    analysis_status="exploratory",
    parent_commit=PARENT,
    target_frame=16,
    per_root_attempts=128,
    maximum_total_attempts=4096,
    per_run_seconds=3,
    beam_width=2,
    maximum_successors=18,
    maximum_depth=4,
    maximum_beam_attempts=126,
    arms=ARMS,
    study_producer_seconds=900,
    study_checker_seconds=900,
    max_rss_bytes=1073741824,
    max_output_bytes=268435456,
    minimum_free_bytes=2147483648,
    max_proposals=4096,
)


def check_plan(plan):
    require(
        all(plan.get(k) == v and type(plan[k]) is type(v) for k, v in FIXED.items()),
        "comparison_contract",
    )
    require(plan["status"] == "preregistered", "comparison_status")
    require(18 * (1 + 2 * (4 - 1)) == 126 <= 128 < 18 * (1 + 3 * (4 - 1)), "width_budget")


def schedule(paths):
    distinct = [p for p in paths if p["representative"] == p["call"]]
    return [
        (p, arm) for i, p in enumerate(distinct) for arm in (ARMS if i % 2 == 0 else ARMS[::-1])
    ]
