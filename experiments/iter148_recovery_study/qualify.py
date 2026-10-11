"""Replay committed qualification evidence before issuing a study admission basis."""

from pathlib import Path
from experiments.iter147_full_horizon_execution.coordinator import read, record, admit, raw_identity
from experiments.iter147_full_horizon_execution.protocol import plan
from experiments.iter146_route_outcome_contract.gpu_check import verify_case
from experiments.iter146_route_outcome_contract.compare import replicas
from .admission import BASE, verify_inputs


def qualify(root):
    root = Path(root)
    inputs_sha = verify_inputs(root)
    prior = root / "experiments/iter147_full_horizon_execution/proof"
    total147 = 0
    for pair in range(4):
        old = read(prior / f"pair_{pair:03d}_analysis.json")
        result = admit(
            root,
            prior / "gpu_raw" / f"pair_{pair:03d}",
            plan(root, "qualification"),
            pair,
            old["raw_commit"],
        )
        if any(result[k] != old[k] for k in result):
            raise ValueError("qualification_replay_changed")
        total147 += result["steps"]
    prior = root / "experiments/iter146_route_outcome_contract/proof"
    total146 = 0
    for arm in ("nominal", "monitor", "brake_t0", "brake_t2_5"):
        old = read(prior / (arm + "_pair_analysis.json"))
        raw = prior / "gpu_raw" / arm
        raw_identity(root, old["raw_commit"], raw)
        cases = [
            verify_case(raw / "runs" / f"scene-0013-easy-00__{arm}__{replica}")
            for replica in (1, 2)
        ]
        replicas(cases)
        if any(r["steps"] != 24 or r["arm"] != arm for r in cases):
            raise ValueError("pulse_qualification_changed")
        total146 += sum(r["steps"] for r in cases)
    result = dict(
        status="supported",
        inputs_sha256=inputs_sha,
        iter147_pairs=4,
        iter147_steps=total147,
        iter146_pairs=4,
        iter146_steps=total146,
        raw_before_replay=True,
    )
    record(root / BASE / "QUALIFICATION.json", result)
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(qualify(Path.cwd()), indent=2))
