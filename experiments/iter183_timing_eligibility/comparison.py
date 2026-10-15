"""Descriptive paired counts and proposal coverage; no planner or geometry calls."""

from .common import require


def coverage(events):
    families = {"initial": 0, "fixed_pattern": 0, "halton": 0}
    evaluations = {}
    for row in events:
        if row["kind"] == "request" and row["evaluation"] is not None and not row["cached"]:
            family = (
                "initial" if row["id"] == 1 else ("fixed_pattern" if row["id"] <= 82 else "halton")
            )
            evaluations[row["evaluation"]] = family
    transitions = dict.fromkeys(families, 0)
    for row in events:
        if row["kind"] == "evaluation":
            family = evaluations[row["id"]]
            families[family] += 1
            transitions[family] += len(row["trace"]) - 1
    return dict(evaluations=families, transitions=transitions)


def compare(records, baseline, iteration=178):
    require(
        baseline["iteration"] == iteration and baseline["phase"] == "closed", "reference_status"
    )
    old = baseline["records"]
    require(len(records) == len(old) == 4, "comparison_population")
    pairs = []
    for new, retained in zip(records, old):
        require(
            new["case"] == retained["case"] and new["seed"] == retained["seed"], "comparison_pair"
        )
        require(
            type(new["complete"]) is bool and type(retained["complete"]) is bool,
            "comparison_outcome",
        )
        pairs.append(
            dict(
                case=new["case"],
                seed=new["seed"],
                reference_complete=retained["complete"],
                complete=new["complete"],
                reference_frame=retained["returned_frame"],
                frame=new["returned_frame"],
                reference_attempts=retained["attempts"],
                attempts=new["attempts"],
                reference_calls=retained["directed_calls"],
                calls=new["directed_calls"],
                reference_edges=retained["accepted_connections"],
                edges=new["accepted_connections"],
                reference_checkpoints=retained["progress_checks"],
                checkpoints=new["progress_checks"],
            )
        )
    return dict(
        reference_iteration=iteration,
        reference_complete_cases=sum(r["reference_complete"] for r in pairs),
        gained_cases=sum(r["complete"] and not r["reference_complete"] for r in pairs),
        lost_cases=sum(r["reference_complete"] and not r["complete"] for r in pairs),
        pairs=pairs,
        boundary="One exposed seed per case. Timing eligibility changes later trees, work and request/coverage; no general control, equal-used-work, latency or superiority claim.",
    )
