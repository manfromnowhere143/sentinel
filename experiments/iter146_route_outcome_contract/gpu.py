"""Finite four-arm full-horizon qualification; no 112-slot study launch path."""

import argparse
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import time

from experiments.iter145_constrained_execution.driver import PipeExchange, plain
from .runner import run
from .resources import output_guard
from experiments.iter145_constrained_execution.resources import IMAGE

CASES = ("scene-0013-easy-00.yaml",)
CONTAINER = "sentinel-i146-qualification-client"
HUGSIM = Path("/opt/sentinel-stack/HUGSIM")
DATA = Path("/datasets/nuscenes-full/hugsim")


def client_command(control, output, episode, arm):
    control, output = Path(control), Path(output)
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        CONTAINER,
        "--gpus",
        "all",
        "--ulimit",
        "fsize=268435456:268435456",
        "--label",
        "sentinel.iter146.episode=" + episode,
        "-v",
        str(control / "e2e146.py") + ":/model/tools/closeloop/e2e.py:ro",
        "-v",
        str(control / "packet") + ":/sentinel:ro",
        "-v",
        "/opt/sentinel-stack/UniAD_SIM:/model:ro",
        "-v",
        "/opt/sentinel-stack/UniAD/ckpts:/model/ckpts:ro",
        "-v",
        "/opt/sentinel-stack/hugsim-shim:/shim:ro",
        "-v",
        str(output) + ":" + str(output),
        "-w",
        "/model",
        "--network",
        "none",
        "-e",
        "PYTHONPATH=/sentinel:/model:/shim",
        "-e",
        "CUDA_VISIBLE_DEVICES=0",
        "-e",
        "SENTINEL_ENABLED=1",
        "-e",
        "SENTINEL_I145_MODE=" + arm,
        "-e",
        "SENTINEL_I145_EPISODE=" + episode,
        "--entrypoint",
        "python",
        IMAGE,
        "-u",
        "tools/closeloop/e2e.py",
        "projects/configs/stage2_e2e/base_e2e.py",
        "ckpts/uniad_base_e2e.pth",
        "--seed",
        "144",
        "--launcher",
        "none",
        "--eval",
        "bbox",
        "--tmpdir",
        "/tmp/iter146",
        "--output",
        str(output),
    ]


def cleanup_client(episode):
    p = subprocess.run(
        [
            "docker",
            "inspect",
            CONTAINER,
            "--format",
            '{{index .Config.Labels "sentinel.iter146.episode"}}',
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if p.returncode != 0:
        # Absence must be observed through docker ps too, rather than treating any error as absent.
        q = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if q.returncode or CONTAINER in q.stdout.splitlines():
            raise RuntimeError("client_cleanup_unobserved")
        return dict(status="absent")
    if p.stdout.strip() != episode:
        raise RuntimeError("client_cleanup_ownership")
    q = subprocess.run(
        ["docker", "rm", "-f", CONTAINER], capture_output=True, text=True, timeout=60
    )
    if q.returncode:
        raise RuntimeError("client_cleanup_failed:" + q.stderr)
    return dict(status="removed", stdout=q.stdout)


def cache_adapter(factory, owned_cache):
    def construct(*args, **kwargs):
        if kwargs.get("cache_location") != "~/.unified_data_cache":
            raise ValueError("unexpected_map_cache_location")
        kwargs["cache_location"] = str(owned_cache)
        return factory(*args, **kwargs)

    return construct


def worker(control, case, arm, replica):
    """Called by an outer process with a hard 600 second deadline."""
    _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    bound = min(256 * 1024**2, hard) if hard != resource.RLIM_INFINITY else 256 * 1024**2
    resource.setrlimit(resource.RLIMIT_FSIZE, (bound, hard))
    import numpy as np
    import torch
    import shapely
    from omegaconf import OmegaConf
    from hugsim_env.envs.hug_sim import HUGSimEnv
    from hugsim_env.envs import hug_sim
    from sim.utils import plan

    if (
        case not in CASES
        or arm not in ("nominal", "monitor", "brake_t0", "brake_t2_5")
        or replica not in (1, 2)
        or not torch.cuda.is_available()
    ):
        raise ValueError("gpu_case_or_device")
    random.seed(144)
    np.random.seed(144)
    torch.manual_seed(144)
    torch.cuda.manual_seed_all(144)
    episode = case.removesuffix(".yaml") + "__" + arm + "__" + str(replica)
    output = control / "runs" / episode
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = dict(
        status="running",
        episode=episode,
        seed=144,
        gpu_observed=False,
        driving_outcome=None,
        live_study_admitted=False,
    )
    (output / "worker_started.json").write_text(json.dumps(receipt, indent=2) + "\n")
    process = None
    render_events = []
    collision_events = []
    try:
        config = OmegaConf.merge(
            {"scenario": OmegaConf.load(DATA / "extracted/scenarios/nuscenes" / case)},
            {"base": OmegaConf.load(control / "nuscenes_base.yaml")},
            {"camera": OmegaConf.load(HUGSIM / "configs/sim/nuscenes_camera.yaml")},
            {"kinematic": OmegaConf.load(HUGSIM / "configs/sim/kinematic.yaml")},
        )
        config.update(
            OmegaConf.load(
                DATA / "extracted/scenes/nuscenes" / config.scenario.scene_name / "cfg.yaml"
            )
        )
        # Same loader and arguments, except a fully inventoried owned cache copy.
        plan.UnifiedDataset = cache_adapter(plan.UnifiedDataset, control / "map_cache")
        for name in ("obs_pipe", "plan_pipe"):
            os.mkfifo(output / name)
        with (output / "client.log").open("xb") as log:
            process = subprocess.Popen(
                client_command(control, output, episode, arm), stdout=log, stderr=subprocess.STDOUT
            )
            env = HUGSimEnv(config, str(output))
            receipt["constructor_seconds"] = time.monotonic() - started
            if not env.gaussians.get_xyz.is_cuda:
                raise RuntimeError("renderer_model_not_cuda")
            renderer = env.render_fn
            foreground, background = hug_sim.fg_collision_det, hug_sim.bg_collision_det

            def measured_foreground(ego_box, objs):
                result = foreground(ego_box, objs)
                collision_events.append(
                    dict(
                        kind="foreground",
                        time=float(env.timestamp),
                        ego_box=plain(ego_box),
                        objects=plain(objs),
                        result=bool(result),
                    )
                )
                return result

            def measured_background(points, box):
                result = background(points, box)
                collision_events.append(
                    dict(
                        kind="background",
                        time=float(env.timestamp),
                        device=str(points.device),
                        points=int(len(points)),
                        result=bool(result),
                    )
                )
                return result

            hug_sim.fg_collision_det, hug_sim.bg_collision_det = (
                measured_foreground,
                measured_background,
            )

            def measured_render(*args, **kwargs):
                torch.cuda.synchronize()
                t = time.perf_counter_ns()
                result = renderer(*args, **kwargs)
                torch.cuda.synchronize()
                image = result["render"]
                if not image.is_cuda or not torch.isfinite(image).all().item():
                    raise RuntimeError("invalid_cuda_render")
                render_events.append(
                    dict(
                        index=len(render_events),
                        time=float(env.timestamp),
                        elapsed_ns=time.perf_counter_ns() - t,
                        device=str(image.device),
                        shape=list(image.shape),
                        transforms={
                            k: m.detach().cpu().tolist() for k, m in kwargs["planning"][0].items()
                        },
                    )
                )
                return result

            env.render_fn = measured_render

            def monitor_reader(frame):
                path = output / "sentinel_iter48_decisions.jsonl"
                if path.is_symlink() or path.stat().st_size > 16 * 1024**2:
                    raise ValueError("monitor_log_boundary")
                raw = path.read_bytes()
                if not raw.endswith(b"\n") or len(raw.splitlines()) != frame + 1:
                    raise ValueError("monitor_log_order")
                return raw.splitlines()[-1]

            summary = run(
                env,
                PipeExchange(output),
                output=output / "trace",
                episode=episode,
                arm=arm,
                monitor_reader=monitor_reader,
                max_actions=24,
                guard=lambda: output_guard(output),
                max_seconds=max(1, 600 - (time.monotonic() - started)),
                device="cuda",
            )
            receipt.update(
                status=summary["status"],
                summary=summary,
                gpu_observed=True,
                cuda_device=torch.cuda.get_device_name(0),
                torch=torch.__version__,
                geos=getattr(shapely, "geos_version_string", None),
                shapely=shapely.__version__,
            )
    except Exception as e:
        receipt.update(status="failed", stop_reason=f"{type(e).__name__}:{e}")
        raise
    finally:
        receipt["render_events"] = render_events
        receipt["collision_events"] = collision_events
        try:
            receipt["cleanup"] = cleanup_client(episode)
        except Exception as e:
            receipt.update(status="failed", cleanup=f"{type(e).__name__}:{e}")
        if process is not None:
            try:
                receipt["client_exit"] = process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                receipt["client_exit"] = process.wait(timeout=15)
        receipt["elapsed_seconds"] = time.monotonic() - started
        (output / "worker.json").write_text(
            json.dumps(plain(receipt), indent=2, allow_nan=False) + "\n"
        )
    return (
        0
        if receipt["status"] == "completed"
        and receipt["summary"]["steps"] == 24
        and receipt["summary"]["stop_reason"] == "action_cap"
        else 1
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--case", choices=CASES, required=True)
    p.add_argument("--arm", choices=("nominal", "monitor", "brake_t0", "brake_t2_5"), required=True)
    p.add_argument("--replica", type=int, choices=(1, 2), required=True)
    a = p.parse_args()
    return worker(a.control, a.case, a.arm, a.replica)


if __name__ == "__main__":
    raise SystemExit(main())
