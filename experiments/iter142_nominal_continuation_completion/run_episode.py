"""New ownership/schedule wrapper around the unchanged Iter141 runner."""

import json
from pathlib import Path

from experiments.iter141_nominal_continuation import run_episode as frozen

CONTROL = Path("/datasets/nuscenes-full/hugsim/iter142_control_20261009")
OUTPUT = Path("/datasets/nuscenes-full/hugsim/outputs/iter142-20261009")
ARMS = ("reference_b", "nominal_a", "nominal_b")


def retained_reference(control=CONTROL):
    packet = control / "packet"
    path = packet / "experiments/iter142_nominal_continuation_completion/INPUTS.json"
    manifest = json.loads(path.read_text())
    if manifest["schema"] != "sentinel.iter142.inputs.v1":
        raise ValueError("retained input schema")
    frozen.check_files(
        {str(packet / name): value["sha256"] for name, value in manifest["files"].items()}
    )


def main():
    retained_reference()
    frozen.CONTROL = CONTROL
    frozen.OUTPUT = OUTPUT
    frozen.ARMS = ARMS
    frozen.CONTAINER = "sentinel-i142-client"
    # Frozen driver filename, schema and I141 environment names are deliberately reused.
    return frozen.main()


if __name__ == "__main__":
    raise SystemExit(main())
