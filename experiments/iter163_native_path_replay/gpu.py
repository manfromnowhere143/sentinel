"""Native GPU scene worker with immutable direct actions and no perception client."""

import json
from pathlib import Path
import random
import resource
import time
from experiments.iter145_constrained_execution.driver import plain
from experiments.iter147_full_horizon_execution.gpu import cache_adapter
from experiments.iter147_full_horizon_execution.resources import guard
from .contract import packet
from .runner import run
from .background import tapped, capture
from .records import read
from .admission import BASE

HUGSIM = Path("/opt/sentinel-stack/HUGSIM")
DATA = Path("/datasets/nuscenes-full/hugsim")


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

    if arm != "selected_maneuver" or replica not in (1, 2) or not torch.cuda.is_available():
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
        env = HUGSimEnv(config, str(output))
        receipt["constructor_seconds"] = time.monotonic() - started
        receipt["actor_types"] = {
            name: type(controller).__name__ for name, controller in env.planner.controller.items()
        }
        if not env.gaussians.get_xyz.is_cuda:
            raise RuntimeError("renderer_model_not_cuda")
        renderer = env.render_fn
        foreground, background = hug_sim.fg_collision_det, hug_sim.bg_collision_det
        binding = read(control / "packet" / BASE / "BACKGROUND.json")
        pending_masks = []
        background = tapped(
            background,
            lambda mask, points, box: pending_masks.append(capture(mask, points, box)),
            binding["predicate_source_sha256"],
        )
        receipt["background_source_sha256"] = binding["predicate_source_sha256"]

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
            if pending_masks:
                raise ValueError("background_tap_order")
            result = background(points, box)
            if len(pending_masks) != 1:
                raise ValueError("background_tap_inventory")
            evidence = pending_masks.pop()
            if evidence["population_sha256"] != binding["arrays"]["selected_xyz"]["sha256"]:
                raise ValueError("native_population_changed")
            if bool(result) != (evidence["count"] > 100):
                raise ValueError("native_predicate_result")
            collision_events.append(
                dict(
                    kind="background",
                    time=float(env.timestamp),
                    device=str(points.device),
                    points=int(len(points)),
                    result=bool(result),
                    **evidence,
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

        selected, geometry = packet(control / "packet")
        summary = run(
            env,
            output=output / "trace",
            slot=slot,
            selected=selected,
            geometry=geometry,
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
        receipt["cleanup"] = {"status": "absent", "scope": "No inference client was launched"}
        receipt["inference_bypassed"] = True
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
