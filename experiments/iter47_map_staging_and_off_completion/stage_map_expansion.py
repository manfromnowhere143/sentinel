#!/usr/bin/env python3
"""Iteration 47 Stage A — official nuScenes map-expansion pack staging (box-side).

Runs ON sentinel-gpu (scp + sudo python3). Implements exactly the Stage-A bars frozen in
HYPOTHESIS.md: preflight free space, download the official Map expansion pack v1.3 to the
archives directory, record byte size + SHA256, scan every zip member for path safety BEFORE
extracting anything, extract into /datasets/nuscenes-full/maps/ only, and verify the four
expansion vector maps exist with the frozen size floor. Emits a redacted-provenance receipts
JSON (scheme, host, basename, bytes, SHA256 — never query strings or credentials).

Source preference per HYPOTHESIS.md: the public motional-nuscenes AWS bucket first; a
Daniel-provided signed URL (uncommitted file via --url-file) as fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

PUBLIC_URL = (
    "https://motional-nuscenes.s3.amazonaws.com/public/v1.0/nuScenes-map-expansion-v1.3.zip"
)
CANONICAL_NAME = "nuScenes-map-expansion-v1.3.zip"
DEST_ROOT = Path("/datasets/nuscenes-full")
ARCHIVE_DIR = DEST_ROOT / "archives"
MAPS_DIR = DEST_ROOT / "maps"
REQUIRED_JSONS = [
    "expansion/singapore-onenorth.json",
    "expansion/singapore-hollandvillage.json",
    "expansion/singapore-queenstown.json",
    "expansion/boston-seaport.json",
]
MIN_JSON_BYTES = 1_000_000
MIN_ARCHIVE_BYTES = 100_000_000
MAX_ARCHIVE_BYTES = 2_000_000_000
MIN_FREE_BYTES = 20 * 1024**3


def redacted_provenance(url: str, source_kind: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    return {
        "source_kind": source_kind,
        "source_scheme": parsed.scheme,
        "source_host": parsed.netloc,
        "source_path_basename": Path(parsed.path).name,
    }


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def member_is_unsafe(name: str, dest: Path) -> bool:
    """True if a zip member would escape dest (absolute path or traversal)."""
    if name.startswith(("/", "\\")) or (len(name) > 1 and name[1] == ":"):
        return True
    resolved = (dest / name).resolve()
    return not str(resolved).startswith(str(dest.resolve()) + "/")


def scan_zip_safety(archive: Path, dest: Path) -> dict:
    unsafe = []
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        for name in names:
            if member_is_unsafe(name, dest):
                unsafe.append(name)
    return {"members_scanned": len(names), "unsafe_members": unsafe}


def download(url: str, target: Path) -> None:
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out, length=1 << 20)
    tmp.rename(target)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url-file", help="uncommitted file holding a signed official URL")
    ap.add_argument("--receipts-out", required=True)
    ap.add_argument("--skip-download", action="store_true",
                    help="archive already staged; hash/extract/verify only")
    args = ap.parse_args()

    receipts: dict = {
        "experiment": "iter47_map_staging_and_off_completion",
        "hypothesis": "experiments/iter47_map_staging_and_off_completion/HYPOTHESIS.md",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "bars": {},
    }

    free = shutil.disk_usage(DEST_ROOT).free
    receipts["preflight_free_bytes"] = free
    receipts["bars"]["preflight_free_space"] = free >= MIN_FREE_BYTES
    if free < MIN_FREE_BYTES:
        print(json.dumps(receipts, indent=2))
        print("I47_STAGE_A_FAIL preflight free space")
        return 1

    if args.url_file:
        url = Path(args.url_file).read_text().strip()
        source_kind = "signed_url"
    else:
        url = PUBLIC_URL
        source_kind = "public_url"
    receipts["source"] = redacted_provenance(url, source_kind)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive = ARCHIVE_DIR / CANONICAL_NAME
    if not args.skip_download or not archive.is_file():
        try:
            download(url, archive)
        except Exception as exc:  # noqa: BLE001 — the failure kind is the receipt
            receipts["download_error"] = f"{type(exc).__name__}: {exc}"
            receipts["bars"]["archive_staged"] = False
            print(json.dumps(receipts, indent=2))
            print("I47_STAGE_A_FAIL download")
            return 1

    size = archive.stat().st_size
    digest = sha256_of(archive)
    receipts["archive"] = {
        "canonical_name": CANONICAL_NAME,
        "remote_path": str(archive),
        "bytes": size,
        "sha256": digest,
    }
    receipts["bars"]["archive_staged"] = True
    receipts["bars"]["archive_bytes_in_range"] = MIN_ARCHIVE_BYTES <= size <= MAX_ARCHIVE_BYTES
    if not receipts["bars"]["archive_bytes_in_range"]:
        print(json.dumps(receipts, indent=2))
        print("I47_STAGE_A_FAIL archive size out of frozen range")
        return 1

    safety = scan_zip_safety(archive, MAPS_DIR)
    receipts["extraction_safety"] = {
        "members_scanned": safety["members_scanned"],
        "unsafe_member_count": len(safety["unsafe_members"]),
        "unsafe_members": safety["unsafe_members"][:20],
    }
    receipts["bars"]["zero_unsafe_members"] = len(safety["unsafe_members"]) == 0
    if safety["unsafe_members"]:
        print(json.dumps(receipts, indent=2))
        print("I47_STAGE_A_FAIL unsafe zip members")
        return 1

    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(MAPS_DIR)

    json_report = {}
    ok = True
    for rel in REQUIRED_JSONS:
        p = MAPS_DIR / rel
        present = p.is_file() and p.stat().st_size >= MIN_JSON_BYTES
        json_report[rel] = {
            "exists": p.is_file(),
            "bytes": p.stat().st_size if p.is_file() else 0,
            "pass": present,
        }
        ok = ok and present
    receipts["expansion_jsons"] = json_report
    receipts["bars"]["four_expansion_jsons"] = ok

    receipts["stage_a_pass"] = all(receipts["bars"].values())
    Path(args.receipts_out).write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps(receipts, indent=2))
    print("I47_STAGE_A_PASS" if receipts["stage_a_pass"] else "I47_STAGE_A_FAIL bars")
    return 0 if receipts["stage_a_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
