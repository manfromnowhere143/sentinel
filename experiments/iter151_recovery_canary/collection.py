"""Bounded raw collection; complete inventories retain the identity of host-only derived files."""

import hashlib
from pathlib import Path
import stat
import tarfile

from .records import read, record
from .ownership import alive
from .remote_ops import idle
from experiments.iter150_cloud_observation.native import file


def archive(control, pair):
    control = Path(control)
    name = f"pair_{pair:03d}"
    owner = read(control / (name + "_owner.json"))
    if alive(owner, owner["binding"]):
        raise ValueError("collection_worker_alive")
    idle()
    document = read(control / "plan.json")
    entries, selected = {}, []
    for slot in document["slots"][pair * 2 : pair * 2 + 2]:
        directory = control / "runs" / slot["id"]
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISFIFO(mode) or stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise ValueError("raw_file_type")
            relative = path.relative_to(control).as_posix()
            entries[relative] = file(control, relative, 256 * 1024**2)
            if path.suffix in (".json", ".jsonl", ".log", ".txt"):
                selected.append(relative)
    for path in sorted(control.glob("*")):
        if path.is_file() and (
            path.name.startswith(name + "_")
            or path.name
            in (
                "execution_manifest.json",
                "plan.json",
                "deployment.json",
                "e2e147.py",
                "nuscenes_base.yaml",
            )
            or path.name in (f"slot_{i:03d}_dispatched.json" for i in (pair * 2, pair * 2 + 1))
        ):
            selected.append(path.name)
    inventory = name + "_output_inventory.json"
    if sum((control / n).stat().st_size for n in selected) > 512 * 1024**2:
        raise ValueError("collection_cap")
    record(
        control / inventory,
        dict(
            files=entries,
            selected_files=selected,
            total_bytes=sum(v["bytes"] for v in entries.values()),
            derived_scope="PLY retained on stopped host with hashes; scalar/event/controller evidence collected",
        ),
    )
    selected.append(inventory)
    destination = control / (name + "_raw.tar.gz")
    with destination.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for relative in selected:
            archive.add(control / relative, arcname=relative, recursive=False)
    value = file(control, destination.name, 256 * 1024**2)
    return dict(pair=pair, **value, files=len(selected))


def extract(archive, destination, expected):
    archive, destination = Path(archive), Path(destination)
    if (
        archive.stat().st_size > 256 * 1024**2
        or type(expected.get("bytes")) is not int
        or not 0 < expected["bytes"] <= 256 * 1024**2
    ):
        raise ValueError("archive_bound")
    raw = archive.read_bytes()
    if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError("archive_identity")
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if (
            not members
            or len({m.name for m in members}) != len(members)
            or sum(m.size for m in members) > 512 * 1024**2
        ):
            raise ValueError("archive_inventory")
        for member in members:
            name = Path(member.name)
            if (
                not member.isfile()
                or name.is_absolute()
                or ".." in name.parts
                or member.size > 256 * 1024**2
            ):
                raise ValueError("archive_path")
        destination.mkdir(parents=True, exist_ok=False)
        for member in members:
            path = destination / member.name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(source.extractfile(member).read())
    return destination
