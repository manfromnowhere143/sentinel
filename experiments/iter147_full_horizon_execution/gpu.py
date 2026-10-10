"""Full-horizon worker over retained runtime components and an explicit slot specification."""

import argparse
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import time

from experiments.iter145_constrained_execution.driver import PipeExchange, plain
from experiments.iter146_route_outcome_contract.runner import run
from .protocol import validate
from .coordinator import read
from .resources import guard
from experiments.iter145_constrained_execution.resources import IMAGE

CONTAINER = "sentinel-i147-client"
HUGSIM = Path("/opt/sentinel-stack/HUGSIM")
DATA = Path("/datasets/nuscenes-full/hugsim")


def client_command(control, output, episode, arm, probe="none"):
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
        "sentinel.iter147.episode=" + episode,
        "-v",
        str(control / "e2e147.py") + ":/model/tools/closeloop/e2e.py:ro",
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
        "SENTINEL_I147_PROBE=" + probe,
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
        "/tmp/iter147",
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
            '{{index .Config.Labels "sentinel.iter147.episode"}}',
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


def worker(control, document, slot):
    """Outer parent owns the inclusive 1,200 second deadline and case directory."""
    case, arm, replica = slot["scenario"], slot["arm"], slot["replica"]
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
        arm not in ("nominal", "monitor", "brake_t0", "brake_t2_5")
        or replica not in (1, 2)
        or not torch.cuda.is_available()
    ):
        raise ValueError("gpu_case_or_device")
    random.seed(144)
    np.random.seed(144)
    torch.manual_seed(144)
    torch.cuda.manual_seed_all(144)
    episode = slot["id"]
    output = control / "runs" / episode
    if (
        not output.is_dir()
        or output.is_symlink()
        or set(p.name for p in output.iterdir()) != {"parent.log"}
    ):
        raise ValueError("exclusive_worker_directory")
    started = time.monotonic()
    receipt = dict(
        status="running",
        episode=episode,
        seed=144,
        gpu_observed=False,
        slot=slot,
        purpose=document["purpose"],
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
                client_command(control, output, episode, arm, slot["probe"]),
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            env = HUGSimEnv(config, str(output))
            receipt["constructor_seconds"] = time.monotonic() - started
            receipt["actor_types"] = {
                name: type(controller).__name__
                for name, controller in env.planner.controller.items()
            }
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
                max_actions=slot["max_actions"],
                guard=lambda: guard(control, output, len(document["slots"])),
                max_seconds=max(1, document["child_seconds"] - (time.monotonic() - started)),
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
        and 0 < receipt["summary"]["steps"] <= slot["max_actions"]
        and receipt["summary"]["stop_reason"] in ("source_terminal", "action_cap")
        else 1
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", type=Path, required=True)
    p.add_argument("--slot", type=int, required=True)
    a = p.parse_args()
    document = read(a.control / "plan.json")
    validate(a.control / "packet", document)
    if not 0 <= a.slot < len(document["slots"]):
        raise ValueError("slot")
    return worker(a.control, document, document["slots"][a.slot])


if __name__ == "__main__":
    raise SystemExit(main())
