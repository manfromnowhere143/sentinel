"""Post-admission descriptions; reads retained evidence and performs no new probes."""

from collections import Counter
import json
from pathlib import Path

from .common import BASE, encode, read, require, sha


def describe(root):
    admitted = json.loads(read(root, BASE / "proof/admission.json"))
    population = json.loads(read(root, BASE / "POPULATION.json"))
    require(admitted["phase"] == "closed", "admission_required")
    original = {r["id"]: r for r in population["records"]}
    cases, details = [], []
    for name in dict.fromkeys(r["case"] for r in admitted["records"]):
        records = [r for r in admitted["records"] if r["case"] == name]
        roots = [r for r in records if r["id"] == r["representative"]]
        cases.append(
            dict(
                case=name,
                node_records=len(records),
                distinct_roots=len(roots),
                checkpoint_roots=sum(
                    any(a["budgeted_checkpoint"] for a in r["arms"]) for r in roots
                ),
                complete_roots=sum(any(a["budgeted_completion"] for a in r["arms"]) for r in roots),
                complete_records=sum(
                    any(a["budgeted_completion"] for a in r["arms"]) for r in records
                ),
                unrequested_complete_records=sum(
                    not original[r["id"]]["outgoing_calls"]
                    and any(a["budgeted_completion"] for a in r["arms"])
                    for r in records
                ),
                stop_wait_complete=sum(r["arms"][0]["budgeted_completion"] for r in roots),
                beam_complete=sum(r["arms"][1]["budgeted_completion"] for r in roots),
                attempts=sum(a["attempts"] for r in roots for a in r["arms"]),
                censored_arms=sum(a["censored"] for r in roots for a in r["arms"]),
            )
        )
        for record in records:
            prior = original[record["id"]]
            node = original[record["representative"]]["node"]
            folder = BASE / "proof/audit_raw" / name / f"node_{node:03d}"
            row = dict(
                id=record["id"],
                frame=record["frame"],
                representative=record["representative"],
                original_requests=len(prior["outgoing_calls"]),
                remaining_attempts=record["remaining_attempts"],
                state=prior["state"],
                arms=[],
            )
            for arm in record["arms"]:
                raw = json.loads(read(root, folder / (arm["method"] + ".json")))
                witness = [raw["rows"][i] for i in (raw["complete_ids"] or [])]
                row["arms"].append(
                    dict(
                        **arm,
                        reason_counts=dict(Counter(r["reason"] for r in raw["rows"][1:])),
                        witness_controls=[
                            dict(frame=r["frame"], action=r["action"], speed=r["state"][3])
                            for r in witness[1:]
                        ],
                        first_complete_program=next(
                            (p for p in raw["programs"] if p["stop"] == "complete"), None
                        ),
                    )
                )
            details.append(row)
    return dict(
        scope="Post-admission descriptive accounting; no new scientific acquisition or causal inference.",
        admission_sha256=sha(read(root, BASE / "proof/admission.json")),
        population_sha256=sha(read(root, BASE / "POPULATION.json")),
        cases=cases,
        records=details,
    )


if __name__ == "__main__":
    value = describe(Path.cwd())
    (Path.cwd() / BASE / "proof/descriptive.json").write_bytes(encode(value))
    print(json.dumps(value["cases"]))
