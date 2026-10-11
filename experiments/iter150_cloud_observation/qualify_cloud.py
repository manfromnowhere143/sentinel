"""One registered CPU-only qualification on the existing VM; no scientific launcher."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from experiments.iter149_observation_recovery.recovery import Limits, reconcile
from experiments.iter149_observation_recovery.replay import check
from .check import verify
from .cloud import BASE, Cloud, VM, VM_ID, recover_start, write
from .native import bind

NATIVE = "/datasets/nuscenes-full/hugsim/iter148_study_20261011"


def script(payload, code):
    return "payload=" + repr(payload) + "\n" + code


def qualify(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path.cwd()
    if shutil.disk_usage(root).free < 15 * 1024**3 + 32 * 1024**2:
        raise ValueError("local_reserve")
    cloud = Cloud(output)
    before = cloud.identity("initial_identity")
    if str(before.get("id")) != VM_ID or before.get("status") != "TERMINATED":
        raise ValueError("initial_provider_state")
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {}
    for directory in ("iter149_observation_recovery", "iter150_cloud_observation"):
        for path in sorted((root / "experiments" / directory).glob("*.py")):
            name = path.relative_to(root).as_posix()
            raw = path.read_bytes()
            if raw != subprocess.check_output(["git", "show", source + ":" + name]):
                raise ValueError("source_not_frozen")
            packet[name] = {"hex": raw.hex(), "sha256": hashlib.sha256(raw).hexdigest()}
    write(
        output / "source.json",
        {"commit": source, "files": {k: v["sha256"] for k, v in packet.items()}},
    )
    start = time.monotonic()
    write(
        output / "budget.json",
        {
            "started_monotonic": start,
            "deadline_monotonic": start + 900,
            "max_seconds": 900,
            "conservative_compute_usd": 0.75,
        },
    )
    log = (output / "watchdog.log").open("xb")
    watcher = subprocess.Popen(
        [sys.executable, "-m", "experiments.iter150_cloud_observation.cloud", str(output)],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    owned = None
    report = {"status": "running", "scientific_outcomes": 0, "cases": []}
    token = uuid.uuid4().hex[:12]
    remote_root = "/var/tmp/sentinel-iter150-" + token
    timer = "sentinel-iter150-" + token + ".timer"
    try:
        write(output / "start_intent.json", {"before": before, "maximum_start_commands": 1})
        started = cloud.run(
            "start",
            ["gcloud", "compute", "instances", "start", VM, *BASE, "--quiet", "--format=json"],
            timeout=120,
        )
        observed_start = cloud.identity("owned_identity")
        if (
            str(observed_start.get("id")) != VM_ID
            or observed_start.get("status") != "RUNNING"
            or observed_start.get("lastStartTimestamp") == before.get("lastStartTimestamp")
        ):
            raise ValueError("new_start_unverified")
        owned = observed_start
        write(output / "owned.json", owned)
        report["start_command_returncode"] = started.returncode
        setup = script(
            {"root": remote_root, "timer": timer, "packet": packet},
            """import hashlib,json,subprocess,time,shutil
from pathlib import Path
r=Path(payload['root']);r.mkdir(exist_ok=False)
assert shutil.disk_usage(r).free>128*1024**2
q=subprocess.run(['systemd-run','--unit',payload['timer'].removesuffix('.timer'),'--on-active=600s','/usr/sbin/shutdown','-h','now'],capture_output=True,text=True,timeout=15)
assert q.returncode==0,q.stderr
for name,row in payload['packet'].items():
 p=r/'packet'/name;p.parent.mkdir(parents=True,exist_ok=True);data=bytes.fromhex(row['hex']);assert hashlib.sha256(data).hexdigest()==row['sha256']
 with p.open('xb') as f:f.write(data)
q=subprocess.run(['systemctl','show',payload['timer'],'--property=ActiveState,NextElapseUSecMonotonic'],capture_output=True,text=True,timeout=5)
assert q.returncode==0 and 'ActiveState=active' in q.stdout
for argv in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 v=subprocess.run(argv,capture_output=True,text=True,timeout=10);assert v.returncode==0 and not v.stdout.strip(),v.stdout
print(json.dumps({'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'timer':q.stdout,'source_files':len(payload['packet']),'free_bytes':shutil.disk_usage(r).free}))
""",
        )
        # Startup SSH failures are observations, never a reason to issue another start.
        setup_result = None
        for attempt in range(3):
            try:
                # Read-only reachability before the one exclusive setup mutation.
                cloud.ssh(
                    f"reachability_{attempt}", 'print("reachable")\n', timeout=30, owned=owned
                )
                break
            except OSError:
                if attempt == 2:
                    raise
                time.sleep(3)
        setup_result = json.loads(cloud.ssh("host_setup", setup, timeout=60, owned=owned))
        write(output / "host_binding.json", dict(setup_result, root=remote_root, timer_unit=timer))
        environment = {
            "vm_id": VM_ID,
            "vm_start": owned["lastStartTimestamp"],
            "host_boot": setup_result["boot"],
            "host_deadline_id": timer,
        }
        original = {}
        for pair in (0, 1, 2):
            local = root / "experiments/iter148_recovery_study/proof/study_raw" / f"pair_{pair:03d}"
            expected, _ = bind(local, pair, environment)
            count = [0]

            def observer(request, timeout):
                index = count[0]
                count[0] += 1
                if pair == 0 and index == 0:
                    write(
                        output / "injected_observation_failure.json",
                        {"scope": "constructed pre-RPC disconnection", "request": request},
                    )
                    raise OSError("injected_disconnect_before_read")
                body = script(
                    {
                        "packet": remote_root + "/packet",
                        "root": NATIVE,
                        "pair": pair,
                        "environment": environment,
                        "expected": expected,
                        "request": request,
                        "timer": timer,
                        "timer_state": setup_result["timer"],
                    },
                    """import sys,json
sys.path.insert(0,payload['packet'])
from experiments.iter150_cloud_observation.remote import observation
print(json.dumps(observation(payload['root'],payload['pair'],payload['environment'],payload['expected'],payload['request'],payload['timer'],payload['timer_state'])))
""",
                )
                value = json.loads(
                    cloud.ssh(f"native_{pair}_{index}", body, timeout=timeout, owned=owned)
                )
                if len(json.dumps(value)) > 512 * 1024:
                    raise OSError("reply_bound")
                raw = bytes.fromhex(value["raw_hex"])
                blobs = {k: bytes.fromhex(v) for k, v in value["blobs_hex"].items()}
                if blobs:
                    original[pair] = blobs["raw"]
                    verify(local, blobs, expected)
                return raw, blobs

            trace = reconcile(
                expected,
                Limits(
                    deadline=min(start + 650, time.monotonic() + 150),
                    max_reads=4 if pair < 2 else 1,
                    max_unavailable=3,
                    read_timeout=45,
                    poll_seconds=1,
                    backoff=(1, 2),
                ),
                f"live-native-{pair}",
                observer,
                time.monotonic,
                time.sleep,
            )
            write(output / f"native_{pair}_trace.json", trace)
            check(trace)
            if pair < 2 and not trace["worker_complete"]:
                raise ValueError("native_completion_unobserved")
            if pair == 2 and (
                trace["worker_complete"] or trace["events"][-1]["state"] != "partial_evidence"
            ):
                raise ValueError("partial_misclassified")
            report["cases"].append(
                {
                    "case": f"native_{pair}",
                    "reason": trace["reason"],
                    "observations": len(trace["events"]),
                }
            )
        launch = script(
            {"root": remote_root},
            """import sys,subprocess,os,json
from pathlib import Path
r=Path(payload['root']);env=dict(os.environ,PYTHONPATH=str(r/'packet'))
rows=[]
for name,seconds,budget in [('complete',0.25,5),('disconnected',20,5)]:
 argv=[sys.executable,'-m','experiments.iter149_observation_recovery.local_host','host',str(r/name),str(seconds),'--budget',str(budget)]
 with (r/(name+'.log')).open('xb') as log:p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 rows.append({'name':name,'pid':p.pid,'argv':argv})
(r/'fixture_launches.json').write_text(json.dumps(rows))
print(json.dumps(rows))
""",
        )
        launches = json.loads(cloud.ssh("fixture_launch", launch, timeout=40, owned=owned))
        write(output / "fixture_launches.json", launches)
        # No read of either worker while active; a permanently lost observer exhausts its bound.
        dummy, _ = bind(
            root / "experiments/iter148_recovery_study/proof/study_raw/pair_000", 0, environment
        )

        def unavailable(request, timeout):
            raise OSError("injected_permanent_observation_loss")

        trace = reconcile(
            dummy,
            Limits(
                deadline=time.monotonic() + 20,
                max_reads=4,
                max_unavailable=4,
                read_timeout=2,
                poll_seconds=1,
                backoff=(1, 2, 4),
            ),
            "permanent-disconnect",
            unavailable,
            time.monotonic,
            time.sleep,
        )
        write(output / "permanent_disconnect_trace.json", trace)
        check(trace)
        if trace["reason"] != "unavailable_limit":
            raise ValueError("disconnect_unbounded")
        collection = script(
            {"root": remote_root},
            """import sys,json,hashlib,subprocess,os
from pathlib import Path
r=Path(payload['root']);env=dict(os.environ,PYTHONPATH=str(r/'packet'));rows={}
for name in ['complete','disconnected']:
 d=r/name;before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in d.iterdir() if p.is_file()}
 closure=json.loads((d/'closure.json').read_text());assert closure['status']=='terminated'
 argv=[sys.executable,'-m','experiments.iter149_observation_recovery.local_host','host',str(d),'1','--budget','2']
 q=subprocess.run(argv,env=env,capture_output=True,timeout=5);assert q.returncode!=0
 after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in d.iterdir() if p.is_file()};assert before==after
 rows[name]={'closure':closure,'duplicate_returncode':q.returncode,'duplicate_stderr':q.stderr.decode(),'files':{p.name:p.read_bytes().hex() for p in d.iterdir() if p.is_file()}}
 assert sum(p.stat().st_size for p in d.iterdir() if p.is_file())<1024**2
print(json.dumps(rows))
""",
        )
        collected = json.loads(cloud.ssh("fixture_collect", collection, timeout=45, owned=owned))
        write(output / "fixtures.json", collected)
        if (
            collected["complete"]["closure"]["returncode"] != 0
            or collected["disconnected"]["closure"]["returncode"] != -9
            or collected["disconnected"]["closure"]["deadline_fired"] is not True
        ):
            raise ValueError("host_deadline_or_completion")
        for name, row in collected.items():
            destination = output / name
            destination.mkdir()
            for filename, data in row["files"].items():
                if Path(filename).name != filename:
                    raise ValueError("collected_path")
                (destination / filename).write_bytes(bytes.fromhex(data))
            report["cases"].append(
                {
                    "case": name,
                    "closure": row["closure"],
                    "duplicate_returncode": row["duplicate_returncode"],
                }
            )
        # Re-attach to completed synthetic evidence through actual IAP and the existing policy.
        host_binding = json.loads(bytes.fromhex(collected["complete"]["files"]["binding.json"]))

        def completed_observer(request, timeout):
            body = script(
                {"root": remote_root, "request": request},
                """import sys,json
sys.path.insert(0,payload['root']+'/packet')
from experiments.iter149_observation_recovery.local_host import observe
raw,blobs=observe(payload['root']+'/complete',payload['request'],5)
print(json.dumps({'raw_hex':raw.hex(),'blobs_hex':{k:v.hex() for k,v in blobs.items()}}))
""",
            )
            value = json.loads(
                cloud.ssh("completion_reconnect", body, timeout=timeout, owned=owned)
            )
            return bytes.fromhex(value["raw_hex"]), {
                k: bytes.fromhex(v) for k, v in value["blobs_hex"].items()
            }

        recovered = reconcile(
            host_binding,
            Limits(deadline=time.monotonic() + 50, max_reads=1, read_timeout=40),
            "reconnect-after-completion",
            completed_observer,
            time.monotonic,
            time.sleep,
        )
        write(output / "completion_reconnect_trace.json", recovered)
        check(recovered)
        if not recovered["worker_complete"]:
            raise ValueError("completion_reconnection")
        post = script(
            {
                "root": remote_root,
                "native": NATIVE,
                "expected": {str(k): base64.b64encode(v).decode() for k, v in original.items()},
                "environment": environment,
                "timer": timer,
                "timer_state": setup_result["timer"],
            },
            """import sys,json,base64,subprocess,hashlib
sys.path.insert(0,payload['root']+'/packet')
from experiments.iter150_cloud_observation.native import bind,observe
from experiments.iter150_cloud_observation.remote import context
current=context(payload['environment'],payload['timer'],payload['timer_state'])
for pair,expected in payload['expected'].items():
 binding,plan=bind(payload['native'],int(pair),current)
 raw,blobs=observe(payload['native'],int(pair),current,binding,'postflight')
 assert blobs['raw']==base64.b64decode(expected)
for argv in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 q=subprocess.run(argv,capture_output=True,text=True,timeout=10);assert q.returncode==0 and not q.stdout.strip()
print(json.dumps({'status':'supported','native_pair_inventories_unchanged':len(payload['expected']),'active_containers':0,'active_gpu_processes':0}))
""",
        )
        postflight = json.loads(cloud.ssh("postflight", post, timeout=45, owned=owned))
        write(output / "postflight.json", postflight)
        report.update(status="supported", postflight=postflight)
    except Exception as exc:
        import traceback

        report.update(status="failed", error=repr(exc), traceback=traceback.format_exc())
    finally:
        if owned is not None:
            try:
                final = cloud.stop("normal_shutdown", owned)
                write(
                    output / "closure.json",
                    {
                        "status": "supported",
                        "instance": final,
                        "elapsed_seconds": time.monotonic() - start,
                    },
                )
                report["termination_verified"] = True
            except Exception as exc:
                report.update(termination_verified=False, closure_error=repr(exc))
        else:
            # Start failures are reconciled by read-only provider observation.
            try:
                current = cloud.identity("unowned_final")
                report["provider_after_unowned_failure"] = current
                if current["status"] == "TERMINATED" and str(current["id"]) == VM_ID:
                    write(
                        output / "closure.json",
                        {
                            "status": "supported",
                            "instance": current,
                            "scope": "no_owned_running_start",
                            "elapsed_seconds": time.monotonic() - start,
                        },
                    )
                elif str(current["id"]) == VM_ID:
                    reconciled = recover_start(cloud, output, "unowned_reconcile")
                    write(output / "reconciled_start.json", reconciled)
                    final = cloud.stop("reconciled_shutdown", reconciled)
                    write(
                        output / "closure.json",
                        {
                            "status": "supported",
                            "instance": final,
                            "scope": "lost_start_reply_reconciled",
                            "elapsed_seconds": time.monotonic() - start,
                        },
                    )
                    report["termination_verified"] = True
            except Exception as exc:
                report["unowned_final_error"] = repr(exc)
        try:
            report["watchdog_exit"] = watcher.wait(timeout=5)
        except subprocess.TimeoutExpired:
            report["watchdog_exit"] = None
        log.close()
        report["elapsed_seconds"] = time.monotonic() - start
        report["conservative_compute_usd"] = report["elapsed_seconds"] * 3 / 3600
        if report.get("termination_verified") is not True or report["elapsed_seconds"] > 900:
            report["status"] = "failed"
        write(output / "result.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = qualify(args.output)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "supported" else 1)
