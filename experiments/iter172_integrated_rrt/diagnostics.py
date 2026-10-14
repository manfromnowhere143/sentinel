"""Post-outcome descriptive audit; no search, tuning or causal attribution.

Necessary endpoint bounds ignore obstacles and coupled dynamics. Excluding a
target does not exclude a useful partial extension toward it. Background labels
on unselected trials retain their producer provenance.
"""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def excluded_by_bounds(before, target, horizon):
    dt = 0.25
    # Semi-implicit motion uses next-step speed. Acceleration <= 2, speed <= 6.
    travel = sum(dt * min(6.0, before[3] + 2.0 * dt * j)
                 for j in range(1, horizon + 1))
    margins = {
        "position": math.hypot(target[0] - before[0], target[1] - before[1])
        - travel - math.sqrt(2.0) * 0.02,
        "speed": abs(target[3] - before[3]) - 2.0 * horizon * dt - 0.01,
        "steering": abs(target[4] - before[4]) - math.pi / 12 * horizon * dt - 0.002,
        "heading": abs((target[2] - before[2] + math.pi) % (2 * math.pi) - math.pi)
        - 0.95 * horizon * dt - 0.002,
    }
    return {key: value for key, value in margins.items() if value > 1e-10}


def summarize(base):
    admission = json.loads((base / "proof/admission.json").read_text())
    records, sources = [], []
    for admitted in admission["records"]:
        path = base / "proof/search_raw" / admitted["case"] / "events.jsonl"
        sources.append({"path": str(path.relative_to(base)),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        calls, evaluations, first_rejections = [], 0, Counter()
        max_frame = 0
        with path.open() as stream:
            for line in stream:
                row = json.loads(line)
                if row["kind"] == "evaluation":
                    evaluations += 1
                    first = next((state["reason"] for state in row["trace"][1:]
                                  if state["reason"] != "clear"), "none")
                    first_rejections[first] += 1
                if row["kind"] != "connection":
                    continue
                task, result = row["task"], row["result"]
                exclusions = excluded_by_bounds(row["before"], row["target"],
                                                task["terminal_frame"]) if task else {}
                calls.append({"call": row["call"], "solved": result is not None,
                              "attempts": result["attempts"] if result else 0,
                              "target_complete": result["target_complete"] if result else False,
                              "stop": row["stop"], "exclusion_margins": exclusions})
                if row.get("trace"):
                    max_frame = max(max_frame, row["trace"][-1]["frame"])
        assert len(calls) == admitted["directed_calls"]
        assert sum(c["attempts"] for c in calls) == admitted["attempts"]
        records.append({"case": admitted["case"], "calls": calls,
                        "evaluations": evaluations,
                        "first_rejections": dict(first_rejections),
                        "maximum_accepted_frame": max_frame})
    calls = [c for r in records for c in r["calls"]]
    excluded = [c for c in calls if c["exclusion_margins"]]
    return {
        "status": "exploratory", "timing": "post-outcome descriptive audit",
        "raw_commit": admission["raw_commit"], "sources": sources,
        "directed_calls": len(calls), "solves": sum(c["solved"] for c in calls),
        "necessarily_unreachable_targets": len(excluded),
        "solved_unreachable_targets": sum(c["solved"] for c in excluded),
        "attempts_on_unreachable_targets": sum(c["attempts"] for c in excluded),
        "exact_target_completions": sum(c["target_complete"] for c in calls),
        "evaluations": sum(r["evaluations"] for r in records),
        "first_background_rejections": sum(r["first_rejections"].get("collision", 0)
                                          for r in records),
        "records": records,
        "boundary": "Necessary endpoint bounds only; partial extensions can help. "
        "Unselected background labels are producer evidence. No causal or repair claim.",
    }


if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    output = directory / "proof/diagnostics.json"
    output.write_text(json.dumps(summarize(directory), indent=2) + "\n")
