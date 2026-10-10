"""Read-only closure of the fourteen frozen scenario files and their declared assets."""

import json
import hashlib
from pathlib import Path
import socket
import subprocess
import time
import yaml
from .resources import file_identity, actor_identity, asset_gate, IMAGE
from .maps import validate as validate_maps

DATA = Path("/datasets/nuscenes-full")
SCENARIOS = DATA / "hugsim/extracted/scenarios/nuscenes"
SCENES = DATA / "hugsim/extracted/scenes/nuscenes"
CARS = DATA / "hugsim/3DRealCar"


def collect(inventory, runtime_files, image_id, actor_files, map_binding=None):
    """Must run on the named host. Missing dependencies remain explicit unavailable rows."""
    if socket.gethostname().split(".")[0] != "sentinel-gpu":
        raise ValueError("asset inspection host identity")
    inspection = subprocess.run(
        ["docker", "image", "inspect", image_id, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    observed_image = inspection.stdout.strip() if inspection.returncode == 0 else None
    result = dict(
        observation_kind="host_readback",
        observed_epoch=time.time(),
        files={},
        scenarios={},
        roles=[],
        image_id=observed_image,
    )
    roles = set()

    def observe(path, role, *, expected=None, small=False):
        key = str(path)
        try:
            if role in ("actor_model", "actor_dimensions"):
                record = actor_identity(CARS, path.parent.relative_to(CARS), path.name, actor_files)
            else:
                record = file_identity(
                    path,
                    max_bytes=4 * 1024**2 if small else 16 * 1024**3,
                    include_bytes=small,
                    allow_empty=role == "runtime_source"
                    and expected == hashlib.sha256(b"").hexdigest(),
                )
            data = record.pop("data", None)
            if expected is not None and record["sha256"] != expected:
                raise ValueError("frozen identity mismatch")
            record.update(status="observed", role=role)
            if key in result["files"] and result["files"][key] != record:
                raise ValueError("asset changed between scenarios")
            result["files"][key] = record
            roles.add(role)
            return data
        except (OSError, ValueError) as exc:
            result["files"][key] = dict(
                status="unavailable",
                bytes=None,
                sha256=None,
                role=role,
                reason=f"{type(exc).__name__}:{exc}",
            )
            return None

    for item in inventory["rows"]:
        if item["role"] != "proposed_pilot":
            continue
        path = SCENARIOS / item["name"]
        row = dict(
            sha256=None,
            dependencies=[str(path)],
            controller_types=[],
            actor_count=None,
            unresolved_dependencies=[],
        )
        result["scenarios"][item["name"]] = row
        data = observe(path, "scenario", expected=item["sha256"], small=True)
        if data is None:
            row["unresolved_dependencies"].append(str(path))
            continue
        row["sha256"] = result["files"][str(path)]["sha256"]
        config = yaml.safe_load(data)
        if not isinstance(config, dict) or not isinstance(config.get("plan_list"), list):
            row["unresolved_dependencies"].append("scenario_plan_list")
            continue
        row["actor_count"] = len(config["plan_list"])
        scene = "scene-" + item["scene"]
        if config["scene_name"] != scene:
            row["unresolved_dependencies"].append("scene_identity")
            continue
        dependencies = [
            (SCENES / scene / "cfg.yaml", "scene_config"),
            (SCENES / scene / "scene.pth", "scene"),
            (SCENES / scene / "ground_param.pkl", "ground"),
        ]
        for actor in config["plan_list"]:
            if not isinstance(actor, list) or len(actor) != 8:
                row["unresolved_dependencies"].append("actor_config")
                continue
            relative = Path(actor[5])
            kind = actor[6]
            if relative.is_absolute() or ".." in relative.parts:
                row["unresolved_dependencies"].append("actor_asset_path")
                continue
            row["controller_types"].append(kind)
            dependencies += [
                (CARS / relative / "gs.pth", "actor_model"),
                (CARS / relative / "wlh.json", "actor_dimensions"),
            ]
            if kind == "UnicyclePlanner":
                uid = actor[7]["uc_id"]
                if type(uid) not in (str, int) or not str(uid).isalnum():
                    row["unresolved_dependencies"].append("unicycle_id")
                    continue
                dependencies.append((SCENES / scene / f"unicycle_{uid}.pth", "unicycle"))
            if kind == "IDM" and not config.get("load_HD_map"):
                row["unresolved_dependencies"].append("idm_route_unavailable")
        # HD-map cache/data closure requires a retained provider inventory, not an
        # assumption that a directory exists. Preserve this unresolved dependency.
        if config.get("load_HD_map"):
            try:
                validate_maps(map_binding)
                for name, identity in map_binding["files"].items():
                    row["dependencies"].append(name)
                    if name not in result["files"]:
                        observe(Path(name), "map_asset", expected=identity["sha256"])
            except (ValueError, KeyError, TypeError):
                row["unresolved_dependencies"].append("HD_map_and_route_cache_manifest_required")
        for path, role in dependencies:
            row["dependencies"].append(str(path))
            observe(path, role)
            if result["files"][str(path)]["status"] != "observed":
                row["unresolved_dependencies"].append(str(path))
        row["controller_types"] = sorted(set(row["controller_types"]))
    # Runtime identities are supplied from the frozen source/deployment packet;
    # missing source, configuration and planner checkpoint bindings fail admission.
    for path, binding in runtime_files.items():
        observe(Path(path), binding["role"], expected=binding["sha256"])
    result["roles"] = sorted(roles)
    try:
        if image_id != IMAGE or any(r["status"] != "observed" for r in result["files"].values()):
            raise ValueError("runtime_or_asset_unavailable")
        asset_gate(inventory, result)
        result.update(status="supported", verdict="ASSET_CLOSURE_OBSERVED")
    except (ValueError, KeyError, TypeError) as exc:
        result.update(status="blocked", verdict="ASSET_CLOSURE_UNAVAILABLE", reason=str(exc))
    return result


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--runtime-files", type=Path, required=True)
    p.add_argument("--image-id", required=True)
    p.add_argument("--actor-files", type=Path, required=True)
    p.add_argument("--map-binding", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = collect(
        json.loads(a.inventory.read_text()),
        json.loads(a.runtime_files.read_text()),
        a.image_id,
        json.loads(a.actor_files.read_text()),
        json.loads(a.map_binding.read_text()) if a.map_binding else None,
    )
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return 0 if result["status"] == "supported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
