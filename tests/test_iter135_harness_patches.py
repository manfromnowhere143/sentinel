from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
ITER135 = REPO / "experiments/iter135_neuroncap_blind_braking_dose_response"


def load(name: str):
    path = ITER135 / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compose_source(patch) -> str:
    return (
        "#!/bin/bash\n"
        + patch.OUTPUT_DECLARATION_ANCHOR
        + "renderer block\n"
        + "if [ $SHOULD_START_MODEL == true ]; then\n"
        + "docker run "
        + patch.ANCHOR
        + "-e SENTINEL_TTC model\n"
        + "docker run --rm --gpus all \\\n"
        + patch.OUTPUT_MOUNT_ANCHOR
        + patch.OUTPUT_LOG_ANCHOR
    )


def test_compose_patch_forwards_dose_environment_to_model_only() -> None:
    patch = load("patch_compose_dose_env.py")
    source = compose_source(patch)

    result = patch.patch_text(source)
    renderer, model = result.split("if [ $SHOULD_START_MODEL == true ]; then", 1)

    assert "SENTINEL_DOSE_" not in renderer
    assert "SENTINEL_RELEASE_K" not in renderer
    for name in (
        "SENTINEL_DOSE_PAIR",
        "SENTINEL_DOSE_ID",
        "SENTINEL_DOSE_SCHEDULE",
        "SENTINEL_RELEASE_K",
    ):
        assert model.count(f"-e {name}") == 1
    assert ': "${SENTINEL_OUTPUT_ROOT:?SENTINEL_OUTPUT_ROOT must be set}"' in result
    assert '--mount "type=bind,src=$SENTINEL_OUTPUT_ROOT,dst=/sentinel_output"' in result
    assert result.splitlines().count("  -v $NUSCENES_PATH:$NUSCENES_PATH:ro \\") == 1
    assert "  -v $NUSCENES_PATH:$NUSCENES_PATH \\" not in result.splitlines()
    assert "--engine.logger.log-dir /sentinel_output/$TIME_NOW/$output_name-$seq" in result
    assert "--engine.logger.log-dir outoutput/" not in result


def test_compose_patch_rejects_ambiguous_anchor() -> None:
    patch = load("patch_compose_dose_env.py")

    try:
        patch.patch_text(compose_source(patch) + patch.ANCHOR)
    except ValueError as exc:
        assert "anchor count" in str(exc)
    else:
        raise AssertionError("ambiguous source was accepted")


@pytest.mark.parametrize(
    "extra_mount",
    (
        "  -v $NUSCENES_PATH:$NUSCENES_PATH \\",
        "  -v $NUSCENES_PATH:$NUSCENES_PATH:rw \\",
        "  -v $NUSCENES_PATH:$NUSCENES_PATH:ro \\",
    ),
)
def test_compose_patch_rejects_rw_or_duplicate_dataset_bind(extra_mount: str) -> None:
    patch = load("patch_compose_dose_env.py")
    source = compose_source(patch).replace(
        patch.OUTPUT_MOUNT_ANCHOR,
        patch.OUTPUT_MOUNT_ANCHOR + extra_mount + "\n",
        1,
    )

    with pytest.raises(ValueError, match="exactly once.*read-only"):
        patch.patch_text(source)


def test_compose_patch_freezes_exact_remote_input_and_output() -> None:
    patch = load("patch_compose_dose_env.py")

    assert patch.EXPECTED_INPUT_SHA256 == (
        "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d"
    )
    assert patch.EXPECTED_OUTPUT_SHA256 == (
        "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada"
    )
