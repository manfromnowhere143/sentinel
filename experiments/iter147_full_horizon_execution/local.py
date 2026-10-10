"""Fixed CPU qualification population; raw production contains no aggregate replay."""

import argparse
import json
from pathlib import Path
from .fixtures import execute

CASES = (
    dict(name="hold", actors=[], mode="hold", max_actions=401),
    dict(name="release", actors=[], mode="release", max_actions=12),
    dict(
        name="actors",
        actors=["AttackPlanner", "ConstantPlanner", "IDM"],
        mode="clear",
        max_actions=32,
    ),
)


def run(root, output):
    output.mkdir(parents=True, exist_ok=False)
    report = dict(
        status="running",
        cases=[],
        scope="CPU constructed assets, identity CUDA transfer, 2x2 renders, synthetic plan/detector input, exact released monitor and actor source slices; no GPU/driving evidence.",
    )
    try:
        for case in CASES:
            for replica in (1, 2):
                name = case["name"] + "__" + str(replica)
                summary = execute(
                    root, output / name, **{k: v for k, v in case.items() if k != "name"}
                )
                report["cases"].append(
                    dict(name=name, specification=case, replica=replica, summary=summary)
                )
                if (
                    summary["status"] != "completed"
                    or summary["steps"] != case["max_actions"]
                    or summary["stop_reason"] != "action_cap"
                ):
                    raise ValueError("incomplete_cpu_case:" + name)
        report["status"] = "completed"
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}:{exc}")
    (output / "population.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = run(a.root, a.output)
    print(
        json.dumps(
            dict(status=result["status"], cases=len(result["cases"]), error=result.get("error"))
        )
    )
    raise SystemExit(0 if result["status"] == "completed" else 1)
