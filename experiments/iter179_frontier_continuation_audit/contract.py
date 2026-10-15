"""Fixed diagnostic population, numerical model and work envelope."""

from .common import require
from .retained import CALLS, REFERENCE, RAW

FIXED = dict(
    iteration=179,
    analysis_status="exploratory",
    minimum_frame=12,
    target_frame=16,
    per_root_attempts=1024,
    maximum_total_attempts=16384,
    aggregate_search_seconds=120,
    beam_width=16,
    audit_producer_seconds=900,
    audit_checker_seconds=900,
    max_rss_bytes=1073741824,
    max_output_bytes=268435456,
    minimum_free_bytes=2147483648,
    endpoint_calls=CALLS,
    parent_commit=REFERENCE,
    retained_raw_commit=RAW,
    selected_case="bend_right",
)


def check_plan(plan):
    require(
        all(plan.get(k) == v and type(plan[k]) is type(v) for k, v in FIXED.items()),
        "audit_contract",
    )
    require(plan["status"] == "preregistered", "audit_status")
