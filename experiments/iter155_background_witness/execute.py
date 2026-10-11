"""One exclusive extraction under an original bounded provider envelope."""

import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
import uuid

from .storage import digest, read_json, write_json, CAP
from experiments.iter150_cloud_observation.cloud import (
    Cloud,
    BASE as CLOUD_ARGS,
    VM,
    recover_start,
    same_start,
)
from experiments.iter154_full_scene_maneuver.execute import provider_shape
from experiments.iter154_full_scene_maneuver.startup import denied_start

BASE = "experiments/iter155_background_witness"
CONTROL = "/datasets/nuscenes-full/hugsim/iter155_background_20261011"
HUGSIM = "/opt/sentinel-stack/HUGSIM"
PYTHON = HUGSIM + "/.pixi/envs/default/bin/python"


def basis(root, source):
    manifest = read_json(root / BASE / "INPUTS.json")
    paths = set(manifest["files"]) | {BASE + "/INPUTS.json", BASE + "/QUALIFICATION.json"}
    packet = {}
    for name in sorted(paths):
        data = (root / name).read_bytes()
        if data != subprocess.check_output(["git", "show", source + ":" + name], cwd=root):
            raise ValueError("unfrozen_source:" + name)
        if (
            name in manifest["files"]
            and {"bytes": len(data), "sha256": digest(data)} != manifest["files"][name]
        ):
            raise ValueError("input_binding")
        packet[name] = {"hex": data.hex(), "sha256": digest(data)}
    if sum(len(r["hex"]) // 2 for r in packet.values()) > 32 * 1024**2:
        raise ValueError("packet_capacity")
    if read_json(root / BASE / "QUALIFICATION.json")["status"] != "supported":
        raise ValueError("qualification")
    return packet


def script(payload, code):
    return "payload=" + repr(payload) + "\n" + code


def extract_archive(raw, destination, inventory):
    if len(raw) > CAP or digest(raw) != inventory["sha256"] or len(raw) != inventory["bytes"]:
        raise ValueError("archive_identity")
    destination.mkdir(exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(inventory["files"]) or {m.name for m in members} != set(
            inventory["files"]
        ):
            raise ValueError("archive_inventory")
        if sum(m.size for m in members) > CAP:
            raise ValueError("archive_capacity")
        for member in members:
            if not member.isfile() or Path(member.name).name != member.name:
                raise ValueError("archive_member")
            expected = inventory["files"][member.name]
            if member.size != expected["bytes"]:
                raise ValueError("archive_member_size")
            data = archive.extractfile(member).read(member.size + 1)
            if len(data) != member.size or digest(data) != expected["sha256"]:
                raise ValueError("archive_member_identity")
            with (destination / member.name).open("xb") as stream:
                stream.write(data)


def retry_wait(budget, result, now, plan):
    if (
        result.get("lifecycle") != "start_denied_capacity"
        or result.get("watchdog_exit") != 0
        or result.get("extraction_launched") is not False
        or not budget["started_monotonic"]
        <= result["finished_monotonic"]
        <= now
        <= budget["deadline_monotonic"]
    ):
        raise ValueError("retry_lifecycle_or_clock")
    delay = max(0, result["finished_monotonic"] + plan["capacity_retry_wait_seconds"] - now)
    if budget["deadline_monotonic"] - now - delay < 1000:
        raise ValueError("retry_remaining_budget")
    return delay


def retry_deadline(root, attempt, plan):
    if type(attempt) is not int or attempt not in (0, 1):
        raise ValueError("attempt")
    if attempt == 0:
        return None
    prior = root / BASE / "proof/attempt_000"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    for name in (
        "result.json",
        "closure.json",
        "budget.json",
        "commands/start.json",
        "commands/start.stderr",
        "commands/initial_identity.stdout",
        "commands/denied_0.stdout",
        "commands/denied_1.stdout",
    ):
        p = prior / name
        if p.read_bytes() != subprocess.check_output(
            ["git", "show", head + ":" + p.relative_to(root).as_posix()], cwd=root
        ):
            raise ValueError("retry_uncommitted")
    result = read_json(prior / "result.json")
    if (
        result.get("lifecycle") != "start_denied_capacity"
        or result.get("watchdog_exit") != 0
        or result.get("extraction_launched") is not False
    ):
        raise ValueError("retry_not_capacity_only")
    denied_start(
        read_json(prior / "commands/initial_identity.stdout"),
        read_json(prior / "commands/start.json")["returncode"],
        (prior / "commands/start.stderr").read_text(),
        [read_json(prior / f"commands/denied_{i}.stdout") for i in range(2)],
    )
    budget = read_json(prior / "budget.json")
    delay = retry_wait(budget, result, time.monotonic(), plan)
    if delay:
        time.sleep(delay)
    return budget


def execute(root, source, attempt):
    root = Path(root).resolve()
    plan = read_json(root / BASE / "STUDY_PLAN.json")
    packet = basis(root, source)
    old_budget = retry_deadline(root, attempt, plan)
    proof = root / BASE / f"proof/attempt_{attempt:03d}"
    proof.mkdir(exist_ok=False)
    if shutil.disk_usage(root).free < 17 * 1024**3:
        raise ValueError("local_reserve")
    cloud = Cloud(proof)
    before = cloud.identity("initial_identity")
    provider_shape(before)
    if before["status"] != "TERMINATED":
        raise ValueError("occupied_provider")
    started = time.monotonic()
    budget = old_budget or {
        "started_monotonic": started,
        "deadline_monotonic": started + plan["cloud_seconds"],
        "max_seconds": plan["cloud_seconds"],
        "conservative_compute_usd": plan["compute_cap_usd"],
    }
    write_json(proof / "budget.json", budget)
    write_json(
        proof / "source_packet.json",
        {"source_commit": source, "files": {p: r["sha256"] for p, r in packet.items()}},
    )
    with (proof / "watchdog.log").open("xb") as log:
        watcher = subprocess.Popen(
            [sys.executable, "-m", "experiments.iter150_cloud_observation.cloud", str(proof)],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    token = uuid.uuid4().hex[:12]
    timer = f"sentinel155-deadline-{token}.timer"
    unit = f"sentinel155-extraction-{token}.service"
    owned = None
    setup = False
    report = {
        "status": "running",
        "extraction_launched": False,
        "new_driving_episodes": 0,
        "attempt": attempt,
    }

    def call(label, payload, code, timeout=90):
        return json.loads(cloud.ssh(label, script(payload, code), timeout=timeout, owned=owned))

    try:
        write_json(proof / "start_intent.json", {"before": before, "maximum_start_commands": 1})
        start = cloud.run(
            "start",
            [
                "gcloud",
                "compute",
                "instances",
                "start",
                VM,
                *CLOUD_ARGS,
                "--quiet",
                "--format=json",
            ],
            timeout=120,
        )
        if start.returncode and b"ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS" in start.stderr:
            closure = denied_start(
                before,
                start.returncode,
                start.stderr.decode(),
                [cloud.identity(f"denied_{i}") for i in range(2)],
            )
            write_json(proof / "closure.json", closure)
            report.update(
                status="inconclusive", lifecycle="start_denied_capacity", termination_verified=True
            )
        else:
            owned = recover_start(cloud, proof, "owned_identity")
            same_start(owned, owned, running=True)
            provider_shape(owned)
            write_json(proof / "owned.json", owned)
            for i in range(4):
                try:
                    cloud.ssh(f"reachability_{i}", 'print("ready")\n', timeout=30, owned=owned)
                    break
                except OSError:
                    if i == 3:
                        raise
                    time.sleep(3)
            remaining = budget["deadline_monotonic"] - time.monotonic()
            if remaining < 900:
                raise ValueError("insufficient_worker_and_closure_time")
            binding = call(
                "setup",
                {
                    "control": CONTROL,
                    "timer": timer,
                    "seconds": int(remaining - 120),
                    "source": source,
                    "packet": packet,
                },
                """import hashlib,json,subprocess,time,shutil
from pathlib import Path
c=Path(payload['control']);c.mkdir(exist_ok=False)
q=subprocess.run(['systemd-run','--unit',payload['timer'].removesuffix('.timer'),'--on-active='+str(payload['seconds'])+'s','/sbin/shutdown','-h','now'],capture_output=True,text=True,timeout=15)
assert q.returncode==0,q.stderr
for argv in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 q=subprocess.run(argv,capture_output=True,text=True,timeout=15);assert q.returncode==0 and not q.stdout.strip()
assert shutil.disk_usage(c).free>100*1024**3
for name,row in payload['packet'].items():
 p=c/'packet'/name;p.parent.mkdir(parents=True,exist_ok=True);data=bytes.fromhex(row['hex']);assert hashlib.sha256(data).hexdigest()==row['sha256']
 with p.open('xb') as f:f.write(data)
q=subprocess.run(['systemctl','show',payload['timer'],'--property=ActiveState,NextElapseUSecMonotonic'],capture_output=True,text=True,timeout=5);assert q.returncode==0 and 'ActiveState=active' in q.stdout
binding={'source_commit':payload['source'],'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'timer':payload['timer'],'timer_readback':q.stdout,'files':len(payload['packet'])}
(c/'binding.json').write_text(json.dumps(binding));print(json.dumps(binding))
""",
                timeout=180,
            )
            setup = True
            write_json(proof / "host_binding.json", binding)
            command = [
                "systemd-run",
                "--wait",
                "--pipe",
                "--collect",
                "--unit",
                unit,
                "--property=RuntimeMaxSec=420",
                "--property=KillMode=control-group",
                "--working-directory=" + HUGSIM,
                "--setenv=PYTHONPATH=" + CONTROL + "/packet:" + HUGSIM,
                "--setenv=PYTHONDONTWRITEBYTECODE=1",
                "--setenv=OPENBLAS_NUM_THREADS=1",
                "--setenv=OMP_NUM_THREADS=1",
                "--setenv=MKL_NUM_THREADS=1",
                PYTHON,
                "-u",
                "-m",
                "experiments.iter155_background_witness.worker",
                CONTROL,
            ]
            write_json(
                proof / "launch_intent.json",
                {"unit": unit, "argv": command, "maximum_worker_invocations": 1},
            )
            report["extraction_launched"] = True
            run = call(
                "extract_once",
                {"argv": command},
                "import json,subprocess\nr=subprocess.run(payload['argv'],capture_output=True,text=True,timeout=450);print(json.dumps({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))\n",
                timeout=510,
            )
            write_json(proof / "worker_reply.json", run)
            if run["returncode"]:
                raise ValueError("extraction_failed")
            report["status"] = "completed"
    except Exception as exc:
        report.update(status="failed", error=repr(exc), traceback=traceback.format_exc())
    finally:
        if owned is not None and setup:
            try:
                cleanup = call(
                    "stop_and_collect",
                    {"control": CONTROL, "unit": unit, "cap": CAP},
                    """import gzip,hashlib,json,subprocess,tarfile,io
from pathlib import Path
c=Path(payload['control']);q=subprocess.run(['systemctl','stop',payload['unit']],capture_output=True,text=True,timeout=30)
active=subprocess.run(['systemctl','is-active',payload['unit']],capture_output=True,text=True,timeout=10)
assert active.stdout.strip() in ('inactive','failed','unknown')
raw=c/'raw';files={};buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
 for p in sorted(raw.iterdir()):
  assert p.is_file() and not p.is_symlink();data=p.read_bytes();assert len(data)<=payload['cap']
  files[p.name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};assert sum(v['bytes'] for v in files.values())<=payload['cap']
  item=tarfile.TarInfo(p.name);item.size=len(data);archive.addfile(item,io.BytesIO(data))
data=buffer.getvalue();assert len(data)<=payload['cap'];archive=c/'raw.tar.gz'
with archive.open('xb') as f:f.write(data)
archive.chmod(0o644)
idle={}
for name,argv in [('containers',['docker','ps','-q']),('gpu_processes',['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'])]:
 q=subprocess.run(argv,capture_output=True,text=True,timeout=15);idle[name]={'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr};assert q.returncode==0 and not q.stdout.strip()
print(json.dumps({'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'files':files,'idle':idle,'unit_inactive':True}))
""",
                    timeout=180,
                )
                write_json(proof / "collection.json", cleanup)
                same_start(cloud.identity("download_before"), owned, running=True)
                q = cloud.run(
                    "download",
                    [
                        "gcloud",
                        "compute",
                        "scp",
                        *CLOUD_ARGS,
                        "--tunnel-through-iap",
                        VM + ":" + CONTROL + "/raw.tar.gz",
                        str(proof / "raw.tar.gz"),
                    ],
                    timeout=180,
                )
                same_start(cloud.identity("download_after"), owned, running=True)
                if q.returncode:
                    raise OSError("download_failed")
                extract_archive(
                    (proof / "raw.tar.gz").read_bytes(), root / BASE / "proof/raw", cleanup
                )
                report["raw_collected"] = True
            except Exception as exc:
                report.update(status="failed", collection_error=repr(exc))
        try:
            if owned is None and report.get("lifecycle") != "start_denied_capacity":
                owned = recover_start(cloud, proof, "closure_recover")
            if owned is not None:
                final = cloud.stop("closure", owned)
                write_json(proof / "closure.json", {"status": "supported", "instance": final})
                report["termination_verified"] = True
        except Exception as exc:
            report.update(status="failed", closure_error=repr(exc), termination_verified=False)
        try:
            report["watchdog_exit"] = watcher.wait(timeout=10)
        except subprocess.TimeoutExpired:
            report["watchdog_exit"] = None
        report["finished_monotonic"] = time.monotonic()
        report["attempt_elapsed_seconds"] = time.monotonic() - started
        report["inclusive_elapsed_seconds"] = time.monotonic() - budget["started_monotonic"]
        report["conservative_compute_usd"] = report["inclusive_elapsed_seconds"] * 3 / 3600
        report["within_budget"] = report["inclusive_elapsed_seconds"] <= plan["cloud_seconds"]
        if report["watchdog_exit"] != 0 or not report["within_budget"]:
            report["status"] = "failed"
        write_json(proof / "result.json", report)
        print(json.dumps(report), flush=True)
    return (
        0
        if report["status"] == "completed"
        else 75
        if report.get("lifecycle") == "start_denied_capacity"
        else 1
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--attempt", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    raise SystemExit(execute(Path.cwd(), args.source, args.attempt))
