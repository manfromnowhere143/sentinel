#!/usr/bin/env python3
"""Stage one official nuScenes trainval archive to the iter28 staging disk.

This is a staging/provenance script, not an extraction or model script. It accepts either one
completed local archive or an uncommitted file containing a signed official download URL, stages the
archive to sentinel-gpu:/datasets/nuscenes-full/archives, verifies remote byte count and SHA256,
and writes a small proof JSON suitable for committing.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT = "sunlit-unison-487018-b0"
ZONE = "us-west1-a"
INSTANCE = "sentinel-gpu"
DEST_ROOT = "/datasets/nuscenes-full"
OUT_DIR = Path("experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads")
ACTIVE_CHUNK_PROCS: set[subprocess.Popen[bytes]] = set()
ACTIVE_CHUNK_PROCS_LOCK = threading.Lock()

EXPECTED: dict[str, str] = {
    "metadata": "v1.0-trainval_meta.tgz",
    "1": "v1.0-trainval01_blobs.tgz",
    "2": "v1.0-trainval02_blobs.tgz",
    "3": "v1.0-trainval03_blobs.tgz",
    "4": "v1.0-trainval04_blobs.tgz",
    "5": "v1.0-trainval05_blobs.tgz",
    "6": "v1.0-trainval06_blobs.tgz",
    "7": "v1.0-trainval07_blobs.tgz",
    "8": "v1.0-trainval08_blobs.tgz",
    "9": "v1.0-trainval09_blobs.tgz",
    "10": "v1.0-trainval10_blobs.tgz",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout, env=env)


def gcloud_base(args: argparse.Namespace) -> list[str]:
    return ["gcloud", "compute", *args.gcloud_prefix]


def remote_ssh(args: argparse.Namespace, command: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        *gcloud_base(args),
        "ssh",
        args.instance,
        "--zone",
        args.zone,
        "--project",
        args.project,
        "--tunnel-through-iap",
        "--quiet",
        "--command",
        command,
    ]
    return run_command(cmd)


def remote_scp(args: argparse.Namespace, local_path: Path, remote_path: str) -> None:
    cmd = [
        *gcloud_base(args),
        "scp",
        str(local_path),
        f"{args.instance}:{remote_path}",
        "--zone",
        args.zone,
        "--project",
        args.project,
        "--tunnel-through-iap",
        "--quiet",
    ]
    run_command(cmd, timeout=None)


def strip_ssh_destination(dry_run_stdout: str) -> tuple[list[str], str]:
    ssh_cmd = shlex.split(dry_run_stdout.strip())
    if not ssh_cmd:
        raise SystemExit("gcloud dry-run returned empty ssh command")
    if "-t" in ssh_cmd:
        ssh_cmd.remove("-t")
    destination = ssh_cmd[-1]
    if "@" not in destination:
        raise SystemExit("gcloud dry-run ssh command missing user@host destination")
    return ssh_cmd[:-1], destination


def rsync_ssh_command(args: argparse.Namespace) -> tuple[list[str], str]:
    if args.rsync_transport == "direct":
        if not args.direct_host:
            raise SystemExit("--direct-host is required with --rsync-transport direct")
        return (
            [
                "/usr/bin/ssh",
                "-i",
                str(args.ssh_key),
                "-o",
                "CheckHostIP=no",
                "-o",
                "HashKnownHosts=no",
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                f"UserKnownHostsFile={args.direct_known_hosts}",
            ],
            f"{args.remote_user}@{args.direct_host}",
        )

    # Let the gcloud IAP tunnel import NumPy for higher throughput; default dry-run uses python -S.
    env = {**os.environ, "CLOUDSDK_PYTHON_SITEPACKAGES": "1"}
    dry_run = run_command(
        [
            *gcloud_base(args),
            "ssh",
            args.instance,
            "--zone",
            args.zone,
            "--project",
            args.project,
            "--tunnel-through-iap",
            "--dry-run",
        ],
        env=env,
    )
    return strip_ssh_destination(dry_run.stdout)


def remote_rsync(args: argparse.Namespace, local_path: Path, remote_path: str) -> None:
    ssh_cmd, destination = rsync_ssh_command(args)
    cmd = [
        "rsync",
        "--append",
        "--partial",
        "--progress",
        "-e",
        shlex.join(ssh_cmd),
        str(local_path),
        f"{destination}:{remote_path}",
    ]
    run_command(cmd, timeout=None)


def parallel_chunk_ranges(total_size: int, chunk_bytes: int) -> list[tuple[int, int, int]]:
    if chunk_bytes <= 0:
        raise SystemExit("--parallel-chunk-bytes must be positive")
    if total_size < 0:
        raise SystemExit("local file size cannot be negative")
    ranges: list[tuple[int, int, int]] = []
    for index, offset in enumerate(range(0, total_size, chunk_bytes)):
        ranges.append((index, offset, min(chunk_bytes, total_size - offset)))
    return ranges


def stream_chunk_over_ssh(
    *,
    local_path: Path,
    offset: int,
    length: int,
    remote_chunk_path: str,
    ssh_cmd: list[str],
    destination: str,
    buffer_bytes: int,
) -> None:
    if buffer_bytes <= 0:
        raise SystemExit("--parallel-buffer-bytes must be positive")
    remote_script = "set -euo pipefail; cat > " + shlex.quote(remote_chunk_path)
    proc = subprocess.Popen(
        [*ssh_cmd, destination, "bash -lc " + shlex.quote(remote_script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    with ACTIVE_CHUNK_PROCS_LOCK:
        ACTIVE_CHUNK_PROCS.add(proc)
    assert proc.stdin is not None
    remaining = length
    try:
        with local_path.open("rb") as f:
            f.seek(offset)
            while remaining:
                data = f.read(min(buffer_bytes, remaining))
                if not data:
                    break
                proc.stdin.write(data)
                remaining -= len(data)
        proc.stdin.close()
    except Exception:
        proc.kill()
        raise

    try:
        stdout = proc.stdout.read().decode(errors="replace") if proc.stdout is not None else ""
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr is not None else ""
        returncode = proc.wait()
    finally:
        with ACTIVE_CHUNK_PROCS_LOCK:
            ACTIVE_CHUNK_PROCS.discard(proc)
    if remaining != 0:
        raise SystemExit(
            f"local chunk read ended early for {remote_chunk_path}: {remaining} bytes remaining"
        )
    if returncode != 0:
        raise SystemExit(
            f"parallel chunk upload failed for {remote_chunk_path}: rc={returncode}\n{stdout}{stderr}"
        )


def terminate_active_chunk_uploads() -> None:
    with ACTIVE_CHUNK_PROCS_LOCK:
        procs = list(ACTIVE_CHUNK_PROCS)
    for proc in procs:
        if proc.poll() is None:
            proc.kill()


def remote_parallel_direct_copy(args: argparse.Namespace, local_path: Path, remote_path: str) -> None:
    if args.rsync_transport != "direct":
        raise SystemExit("--transfer-method parallel-direct requires --rsync-transport direct")
    if args.parallel_workers <= 0:
        raise SystemExit("--parallel-workers must be positive")

    ssh_cmd, destination = rsync_ssh_command(args)
    total_size = local_path.stat().st_size
    ranges = parallel_chunk_ranges(total_size, args.parallel_chunk_bytes)
    if not ranges:
        raise SystemExit("refusing parallel upload of empty file")

    parts_dir = f"{remote_path}.parts"
    assembled_path = f"{remote_path}.assembled"
    q_parts_dir = shlex.quote(parts_dir)
    q_assembled = shlex.quote(assembled_path)
    q_remote_path = shlex.quote(remote_path)
    q_remote_user = shlex.quote(args.remote_user)
    remote_ssh(
        args,
        (
            "sudo bash -lc "
            + shlex.quote(
                "set -euo pipefail; "
                f"rm -rf {q_parts_dir} {q_assembled}; "
                f"mkdir -p {q_parts_dir}; "
                f"chown {q_remote_user}:{q_remote_user} {q_parts_dir}; "
                f"chmod 0700 {q_parts_dir}"
            )
        ),
    )

    workers = min(args.parallel_workers, len(ranges))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                stream_chunk_over_ssh,
                local_path=local_path,
                offset=offset,
                length=length,
                remote_chunk_path=f"{parts_dir}/part-{index:06d}",
                ssh_cmd=ssh_cmd,
                destination=destination,
                buffer_bytes=args.parallel_buffer_bytes,
            ): (index, length)
            for index, offset, length in ranges
        }
        try:
            for future in concurrent.futures.as_completed(futures):
                index, length = futures[future]
                future.result()
                print(f"ITER28_CHUNK_UPLOADED index={index} bytes={length}", flush=True)
        except KeyboardInterrupt:
            terminate_active_chunk_uploads()
            raise

    remote_ssh(
        args,
        (
            "sudo bash -lc "
            + shlex.quote(
                "set -euo pipefail; "
                f"rm -f {q_assembled}; "
                f"cat {q_parts_dir}/part-* > {q_assembled}; "
                f"test \"$(stat -c %s {q_assembled})\" = {total_size}; "
                f"mv -f {q_assembled} {q_remote_path}; "
                f"chown {q_remote_user}:{q_remote_user} {q_remote_path}; "
                f"rm -rf {q_parts_dir}"
            )
        ),
    )


def read_signed_url(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"missing signed URL file: {path}")
    url = path.read_text().strip()
    if "\n" in url or "\r" in url:
        raise SystemExit("signed URL file must contain exactly one URL")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SystemExit("signed URL must be an https URL with a host")
    return url


def redacted_url_source(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    return {
        "source_host": parsed.netloc,
        "source_path_basename": Path(parsed.path).name,
        "source_scheme": parsed.scheme,
    }


def parse_remote_verify(stdout: str) -> tuple[int, str]:
    size: int | None = None
    digest: str | None = None
    for line in stdout.splitlines():
        if line.startswith("ITER28_REMOTE_SIZE "):
            size = int(line.split()[1])
        if line.startswith("ITER28_REMOTE_SHA256 "):
            digest = line.split()[1]
    if size is None or digest is None:
        raise SystemExit("remote verification output missing size or sha256")
    return size, digest


def validate_local_path(path: Path, canonical_name: str, package: str) -> None:
    if not path.is_file():
        raise SystemExit(f"missing local archive: {path}")
    if path.name.endswith(".crdownload"):
        raise SystemExit(f"refusing active partial Chrome download: {path}")
    if package != "metadata" and path.name != canonical_name:
        raise SystemExit(f"expected local basename {canonical_name}, got {path.name}")
    if package == "metadata" and not path.name.startswith("v1.0-trainval_meta"):
        raise SystemExit(f"expected metadata archive basename, got {path.name}")
    if path.stat().st_size <= 0:
        raise SystemExit(f"refusing empty archive: {path}")


def proof_payload(
    *,
    args: argparse.Namespace,
    canonical_name: str,
    local_path: Path | None,
    local_size: int | None,
    local_sha256: str | None,
    remote_size: int,
    remote_sha256: str,
    preflight_stdout: str,
    verify_stdout: str,
    source_kind: str,
    transfer_method: str,
    source_redacted: dict[str, str] | None = None,
) -> dict[str, Any]:
    archive: dict[str, Any] = {
        "canonical_name": canonical_name,
        "package": args.package,
        "remote_path": f"{args.dest_root}/archives/{canonical_name}",
        "remote_sha256": remote_sha256,
        "remote_size_bytes": remote_size,
    }
    if local_path is not None:
        archive.update(
            {
                "local_basename": local_path.name,
                "local_path": str(local_path),
                "local_sha256": local_sha256,
                "local_size_bytes": local_size,
                "sha256_match": local_sha256 == remote_sha256,
                "size_match": local_size == remote_size,
            }
        )
    if source_redacted is not None:
        archive.update(source_redacted)

    return {
        "archive": {
            **archive,
        },
        "command": shlex.join([sys.executable, *sys.argv]),
        "destination": {
            "dest_root": args.dest_root,
            "instance": args.instance,
            "project": args.project,
            "zone": args.zone,
        },
        "experiment": "iter28_nuscenes_trainval_staging",
        "hypothesis": "experiments/iter28_nuscenes_trainval_staging/HYPOTHESIS.md",
        "preflight_stdout": preflight_stdout,
        "source_kind": source_kind,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "transfer_method": transfer_method,
        "verify_stdout": verify_stdout,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, choices=sorted(EXPECTED))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--local-path", type=Path)
    source.add_argument(
        "--signed-url-file",
        type=Path,
        help="uncommitted file containing one signed official URL; URL is not committed",
    )
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--zone", default=ZONE)
    parser.add_argument("--instance", default=INSTANCE)
    parser.add_argument("--dest-root", default=DEST_ROOT)
    parser.add_argument("--remote-user", default="danielwahnich")
    parser.add_argument("--transfer-method", choices=("rsync", "scp", "parallel-direct"), default="rsync")
    parser.add_argument("--rsync-transport", choices=("iap", "direct"), default="iap")
    parser.add_argument("--direct-host")
    parser.add_argument("--direct-known-hosts", default="/private/tmp/sentinel_direct_known_hosts")
    parser.add_argument("--ssh-key", default="/Users/danielwahnich/.ssh/google_compute_engine", type=Path)
    parser.add_argument("--parallel-workers", type=int, default=4)
    parser.add_argument("--parallel-chunk-bytes", type=int, default=256 * 1024 * 1024)
    parser.add_argument("--parallel-buffer-bytes", type=int, default=4 * 1024 * 1024)
    parser.add_argument("--out-dir", default=str(OUT_DIR), type=Path)
    parser.add_argument(
        "--gcloud-prefix",
        nargs="*",
        default=[],
        help="reserved for tests; do not use in production",
    )
    args = parser.parse_args()

    canonical_name = EXPECTED[args.package]
    local_path: Path | None = None
    local_size: int | None = None
    local_sha256: str | None = None
    signed_url: str | None = None
    source_redacted: dict[str, str] | None = None
    if args.local_path is not None:
        local_path = args.local_path.expanduser().resolve()
        validate_local_path(local_path, canonical_name, args.package)
        local_size = local_path.stat().st_size
        local_sha256 = sha256_file(local_path)
        source_kind = "local_path"
    else:
        signed_url = read_signed_url(args.signed_url_file.expanduser().resolve())
        source_redacted = redacted_url_source(signed_url)
        source_kind = "signed_url"

    q_dest_root = shlex.quote(args.dest_root)
    q_archives = shlex.quote(f"{args.dest_root}/archives")
    q_tmp_dir = shlex.quote(f"{args.dest_root}/.iter28_tmp")
    q_remote_user = shlex.quote(args.remote_user)
    preflight = remote_ssh(
        args,
        (
            "sudo bash -lc "
            + shlex.quote(
                "set -euo pipefail; "
                f"test -d {q_dest_root}; "
                f"mkdir -p {q_archives}; "
                f"mkdir -p {q_tmp_dir}; "
                f"chown {q_remote_user}:{q_remote_user} {q_tmp_dir}; "
                f"chmod 0700 {q_tmp_dir}; "
                f"df -B1 {q_dest_root}; "
                "docker ps --format '{{.Names}}'"
            )
        ),
    )

    remote_tmp = f"{args.dest_root}/.iter28_tmp/iter28-upload-{canonical_name}"
    if local_path is not None:
        if args.transfer_method == "rsync":
            remote_rsync(args, local_path, remote_tmp)
            transfer_method = f"rsync_{args.rsync_transport}"
        elif args.transfer_method == "scp":
            remote_scp(args, local_path, remote_tmp)
            transfer_method = "scp_iap"
        else:
            remote_parallel_direct_copy(args, local_path, remote_tmp)
            transfer_method = "parallel_direct"
    else:
        assert signed_url is not None
        remote_url_file = f"{args.dest_root}/.iter28_tmp/iter28-url-{canonical_name}.txt"
        fd, url_file_name = tempfile.mkstemp(
            prefix=f"iter28-{canonical_name}-",
            suffix=".curl-config",
            text=True,
        )
        url_file = Path(url_file_name)
        try:
            with open(fd, "w") as f:
                f.write(f"url = {json.dumps(signed_url)}\n")
            remote_scp(args, url_file, remote_url_file)
            q_url_file = shlex.quote(remote_url_file)
            q_tmp = shlex.quote(remote_tmp)
            remote_ssh(
                args,
                (
                    "sudo bash -lc "
                    + shlex.quote(
                        "set -euo pipefail; "
                        f"chmod 0600 {q_url_file}; "
                        f"trap 'rm -f {q_url_file}' EXIT; "
                        f"curl --fail --location --silent --show-error --retry 5 "
                        f"--retry-delay 10 --connect-timeout 30 --output {q_tmp} "
                        f"--config {q_url_file}"
                    )
                ),
            )
            transfer_method = "curl_signed_url"
        finally:
            url_file.unlink(missing_ok=True)

    q_tmp = shlex.quote(remote_tmp)
    q_remote = shlex.quote(f"{args.dest_root}/archives/{canonical_name}")
    verify = remote_ssh(
        args,
        (
            "sudo bash -lc "
            + shlex.quote(
                "set -euo pipefail; "
                f"install -m 0644 {q_tmp} {q_remote}; "
                f"rm -f {q_tmp}; "
                f"echo ITER28_REMOTE_SIZE $(stat -c %s {q_remote}); "
                f"echo ITER28_REMOTE_SHA256 $(sha256sum {q_remote} | awk '{{print $1}}')"
            )
        ),
    )
    remote_size, remote_sha256 = parse_remote_verify(verify.stdout)
    if local_size is not None and remote_size != local_size:
        raise SystemExit(f"remote size mismatch: local={local_size} remote={remote_size}")
    if local_sha256 is not None and remote_sha256 != local_sha256:
        raise SystemExit(f"remote sha256 mismatch: local={local_sha256} remote={remote_sha256}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    proof = proof_payload(
        args=args,
        canonical_name=canonical_name,
        local_path=local_path,
        local_size=local_size,
        local_sha256=local_sha256,
        remote_size=remote_size,
        remote_sha256=remote_sha256,
        preflight_stdout=preflight.stdout,
        verify_stdout=verify.stdout,
        source_kind=source_kind,
        transfer_method=transfer_method,
        source_redacted=source_redacted,
    )
    proof_path = args.out_dir / f"{canonical_name}.json"
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    print(f"ITER28_UPLOADED {canonical_name} bytes={remote_size} sha256={remote_sha256}")
    print(f"ITER28_PROOF {proof_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
