#!/usr/bin/env python3
"""Read-only staging-remedy discovery for iter26.

This script inspects direct root/parent metadata and disk capacity only. It does not download,
copy, extract, delete, symlink, launch Docker, import UniAD, run NeuroNCAP, or read image bytes.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any


EXPERIMENT = "iter26_data_staging_remedy"
HYPOTHESIS = "experiments/iter26_data_staging_remedy/HYPOTHESIS.md"
REFERENCE = "experiments/iter26_data_staging_remedy/official_nuscenes_download_reference.md"
FROZEN_ROOTS = (
    "/datasets/nuscenes",
    "/datasets/nuscenes-full",
    "/opt/sentinel-stack/data/nuscenes",
    "/opt/sentinel-stack/UniAD/data/nuscenes",
    "/data/nuscenes",
)
PARENTS_TO_LIST = (
    "/datasets",
    "/opt/sentinel-stack/data",
    "/opt/sentinel-stack/UniAD/data",
    "/data",
)
TRAINVAL_BLOB_GB = (
    29.41,
    28.06,
    27.81,
    29.87,
    26.25,
    25.61,
    27.50,
    28.19,
    31.21,
    38.87,
)
BYTES_PER_GB = 1_000_000_000
CAPACITY_MARGIN = 1.25


def disk_report(path: Path) -> dict[str, Any]:
    exists = path.exists()
    target = path if exists else path.parent
    while not target.exists() and target != target.parent:
        target = target.parent
    if not target.exists():
        return {"exists": exists, "path": str(path), "status": "no_existing_parent"}
    usage = shutil.disk_usage(target)
    return {
        "exists": exists,
        "free_bytes": int(usage.free),
        "free_gb_decimal": round(usage.free / BYTES_PER_GB, 3),
        "path": str(path),
        "status": "ok",
        "usage_probe_path": str(target),
    }


def direct_parent_listing(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"entries": [], "path": str(path), "status": "missing_parent"}
    if not path.is_dir():
        return {"entries": [], "path": str(path), "status": "not_directory"}
    entries = []
    try:
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            entries.append(
                {
                    "is_dir": child.is_dir(),
                    "is_symlink": child.is_symlink(),
                    "name": child.name,
                }
            )
    except OSError as exc:
        return {"entries": [], "error": str(exc), "path": str(path), "status": "list_error"}
    return {"entries": entries, "path": str(path), "status": "ok"}


def direct_root_probe(path: Path) -> dict[str, Any]:
    samples = path / "samples"
    meta = path / "v1.0-trainval"
    return {
        "has_samples_dir": samples.is_dir(),
        "has_trainval_metadata_dir": meta.is_dir(),
        "path": str(path),
        "root_exists": path.exists(),
        "root_is_dir": path.is_dir(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="experiments/iter26_data_staging_remedy/staging_remedy_discovery.json",
        help="output JSON path",
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_archive_gb = sum(TRAINVAL_BLOB_GB)
    total_archive_bytes = int(round(total_archive_gb * BYTES_PER_GB))
    required_free_bytes = int(round(total_archive_bytes * CAPACITY_MARGIN))

    capacity = [disk_report(Path(root)) for root in FROZEN_ROOTS]
    best_capacity = max(
        (entry.get("free_bytes", 0) for entry in capacity if entry.get("status") == "ok"),
        default=0,
    )
    discovery = {
        "capacity_bar": {
            "best_free_bytes": int(best_capacity),
            "best_free_gb_decimal": round(best_capacity / BYTES_PER_GB, 3),
            "margin": CAPACITY_MARGIN,
            "pass": best_capacity >= required_free_bytes,
            "required_free_bytes": required_free_bytes,
            "required_free_gb_decimal": round(required_free_bytes / BYTES_PER_GB, 3),
        },
        "command": shlex.join([sys.executable, *sys.argv]),
        "data_movement_bytes": 0,
        "experiment": EXPERIMENT,
        "frozen_roots": list(FROZEN_ROOTS),
        "hypothesis": HYPOTHESIS,
        "official_reference": REFERENCE,
        "parent_listings": [direct_parent_listing(Path(parent)) for parent in PARENTS_TO_LIST],
        "root_capacity": capacity,
        "root_probes": [direct_root_probe(Path(root)) for root in FROZEN_ROOTS],
        "source_candidate": {
            "archive_count": len(TRAINVAL_BLOB_GB),
            "archive_sizes_gb_decimal": list(TRAINVAL_BLOB_GB),
            "name": "official_nuscenes_v1_0_trainval_file_blobs_parts_1_10",
            "source_type": "official_nuscenes_download",
            "total_archive_bytes": total_archive_bytes,
            "total_archive_gb_decimal": round(total_archive_gb, 3),
        },
        "stage": "read_only_staging_remedy_discovery",
    }

    out_path.write_text(json.dumps(discovery, indent=2, sort_keys=True) + "\n")
    print(
        "iter26 staging discovery "
        f"capacity_pass={discovery['capacity_bar']['pass']} "
        f"required_free_gb={discovery['capacity_bar']['required_free_gb_decimal']} "
        f"best_free_gb={discovery['capacity_bar']['best_free_gb_decimal']} "
        f"out={out_path}"
    )
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    raise SystemExit(main())
