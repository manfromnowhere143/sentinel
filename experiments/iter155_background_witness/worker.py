"""One bounded source/scene extraction. No simulator constructor, reset, step or render."""

import argparse
import json
from pathlib import Path
import pickle
import resource
import shutil
import time

from .storage import digest, put_array, read_json, write_json, CAP
from .source import background_function, box_statements
from experiments.iter150_cloud_observation.native import file

HUGSIM = Path("/opt/sentinel-stack/HUGSIM")
SCENE = Path("/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0013")


def check_assets(assets):
    for name, expected in assets.items():
        observed = file(Path("/"), name.lstrip("/"), expected["bytes"])
        if observed != expected:
            raise ValueError("asset_identity:" + name)
    return len(assets)


def extract(control):
    import numpy as np
    import torch
    from omegaconf import OmegaConf
    from gaussian_renderer import GaussianModel
    from hugsim_env.envs.hug_sim import HUGSimEnv
    from sim.utils.sim_utils import dense_cam_poses

    base = control / "packet/experiments/iter155_background_witness"
    plan = read_json(base / "STUDY_PLAN.json")
    assets = read_json(base / "ASSETS.json")
    output = control / "raw"
    output.mkdir(exist_ok=False)
    write_json(
        control / "extraction_initialized.json",
        {
            "status": "running",
            "source_commit": read_json(control / "binding.json")["source_commit"],
            "new_driving_episodes": 0,
        },
    )
    started = time.monotonic()
    report = {
        "status": "running",
        "arrays": {},
        "frames": [],
        "new_driving_episodes": 0,
        "constructor_reset_step_render_calls": 0,
    }
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (CAP, CAP))
        if not torch.cuda.is_available() or shutil.disk_usage(control).free < 100 * 1024**3:
            raise ValueError("device_or_reserve")
        report["preflight_files"] = check_assets(assets)
        cfg = OmegaConf.load(SCENE / "cfg.yaml")
        model = GaussianModel(cfg.model.sh_degree, affine=cfg.affine)
        parameters, iteration = torch.load(SCENE / "scene.pth", weights_only=False)
        model.restore(parameters, None)
        xyz = model.get_xyz.detach()
        features = model.get_3D_features.detach()
        opacity = model.get_opacity[:, 0].detach()
        n = len(xyz)
        if not (
            0 < n <= plan["max_population"]
            and xyz.shape == (n, 3)
            and features.ndim == 2
            and 1 < features.shape[1] <= plan["max_features"]
        ):
            raise ValueError("population_shape")
        if not all(
            v.is_cuda and v.dtype == torch.float32 and torch.isfinite(v).all().item()
            for v in (xyz, features, opacity)
        ):
            raise ValueError("population_values")
        labels = torch.argmax(features, dim=-1, keepdim=True)
        selected = ((labels > 1) & (labels != 10))[:, 0] & (opacity > 0.8)
        points = xyz[selected]
        arrays = report["arrays"]
        for name, value in [
            ("population_xyz", xyz),
            ("population_features", features),
            ("population_opacity", opacity),
            ("selected_xyz", points),
        ]:
            put_array(output, name, value.cpu().numpy().astype("<f4", copy=False), arrays)
        put_array(output, "selection", selected.cpu().numpy().astype("u1"), arrays)
        with (SCENE / "ground_param.pkl").open("rb") as stream:
            poses, height, commands = pickle.load(stream)
        dense, _ = dense_cam_poses(poses, commands)
        put_array(output, "ground_poses", dense.astype("<f8"), arrays)
        source_env = (HUGSIM / "sim/hugsim_env/envs/hug_sim.py").read_text()
        source_collision = (HUGSIM / "sim/utils/score_calculator.py").read_text()
        native = background_function(source_collision, torch)
        mask_function = background_function(source_collision, torch, mask=True)
        for frame in plan["unique_frames"]:
            old = next(f for f in plan["frames"] if f["frame"] == frame)
            env = object.__new__(HUGSimEnv)
            env.ground_model = (dense, height, commands)
            env.vab = np.array([old["state"][1], old["state"][0]])
            env.vr = np.array([0.0, old["state"][2], 0.0])
            box_statements(source_env, env, np)
            position = env.vt
            verts = (env.ego[:3, :3] @ env.ego_verts.T).T + env.ego[:3, 3]
            box = torch.from_numpy(verts.astype(np.float32)).cuda()
            result = native(points, box)
            mask = mask_function(points, box)
            torch.cuda.synchronize()
            count = int(mask.sum().item())
            if bool(result) != (count > 100):
                raise ValueError("native_mask_return_mismatch")
            put_array(output, f"box_{frame}", box.cpu().numpy().astype("<f4"), arrays)
            put_array(output, f"mask_{frame}", mask.cpu().numpy().astype("u1"), arrays)
            report["frames"].append(
                {
                    "frame": frame,
                    "time": old["time"],
                    "position": position.tolist(),
                    "rotation": env.vr.tolist(),
                    "count": count,
                    "collision": bool(result),
                    "points": len(points),
                }
            )
        report["sources"] = {}
        sources = [
            "sim/hugsim_env/envs/hug_sim.py",
            "sim/utils/score_calculator.py",
            "sim/utils/sim_utils.py",
            "scene/gaussian_model.py",
            "scene/ground_model.py",
        ]
        for source in sources:
            data = (HUGSIM / source).read_bytes()
            name = Path(source).name + ".txt"
            (output / name).write_bytes(data)
            report["sources"][name] = {
                "bytes": len(data),
                "sha256": digest(data),
                "original": str(HUGSIM / source),
            }
        report["configuration"] = {
            "scene_config": OmegaConf.to_container(cfg, resolve=True),
            "checkpoint_iteration": int(iteration),
            "scene_sha256": assets[str(SCENE / "scene.pth")]["sha256"],
            "ground_sha256": assets[str(SCENE / "ground_param.pkl")]["sha256"],
        }
        report["numeric_environment"] = {
            "torch": torch.__version__,
            "numpy": np.__version__,
            "gpu": torch.cuda.get_device_name(0),
            "cuda": torch.version.cuda,
            "allow_tf32": torch.backends.cuda.matmul.allow_tf32,
            "float32_matmul_precision": torch.get_float32_matmul_precision(),
        }
        report["selected_points"] = len(points)
        report["population_points"] = n
        if sum(row["bytes"] for row in arrays.values()) > CAP:
            raise ValueError("output_capacity")
        report["status"] = "completed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = repr(exc)
        raise
    finally:
        try:
            report["postflight_files"] = check_assets(assets)
        except Exception as exc:
            report["status"] = "failed"
            report["postflight_error"] = repr(exc)
        report["elapsed_seconds"] = time.monotonic() - started
        write_json(output / "witness.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("control", type=Path)
    args = parser.parse_args()
    result = extract(args.control)
    print(
        json.dumps(
            {
                "status": result["status"],
                "frames": result["frames"],
                "selected_points": result["selected_points"],
            }
        ),
        flush=True,
    )

    raise SystemExit(0 if result["status"] == "completed" else 1)
