"""Read-only entrypoint deployed to the owned qualification directory."""

from pathlib import Path
import subprocess
import urllib.request

from .native import observe


def context(environment, timer, expected_timer):
    request = urllib.request.Request(
        "http://metadata.google.internal/computeMetadata/v1/instance/id",
        headers={"Metadata-Flavor": "Google"},
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        vm_id = response.read(128).decode().strip()
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    query = subprocess.run(
        ["systemctl", "show", timer, "--property=ActiveState,NextElapseUSecMonotonic"],
        capture_output=True,
        text=True,
        timeout=3,
    )
    if (
        query.returncode
        or query.stdout != expected_timer
        or "ActiveState=active" not in query.stdout
    ):
        raise OSError("host_deadline_changed_or_unavailable")
    return dict(environment, vm_id=vm_id, host_boot=boot, host_deadline_id=timer)


def observation(root, pair, environment, expected, request, timer, expected_timer):
    current = context(environment, timer, expected_timer)
    raw, blobs = observe(root, pair, current, expected, request, alive=False)
    return {"raw_hex": raw.hex(), "blobs_hex": {k: v.hex() for k, v in blobs.items()}}
