"""Registered finite-block execution. Every launch is exclusive; observation retries are read-only."""

import argparse
import base64
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

from .admission import BASE, PLAN, basis, history, identity, remaining, validate_plan
from .records import read, record
from .collection import extract
from .remote_ops import CONTROL, PYTHON
from experiments.iter149_observation_recovery.recovery import Limits, reconcile
from experiments.iter149_observation_recovery.replay import check
from experiments.iter150_cloud_observation.cloud import (
    BASE as CLOUD_ARGS,
    Cloud,
    VM,
    VM_ID,
    recover_start,
    same_start,
)


def rpc(payload, code, *, runtime=True):
    body = "payload=" + repr(payload) + "\n" + code
    if not runtime:
        return body
    return (
        "import os,subprocess,sys\n"
        + "env=dict(os.environ,PYTHONPATH="
        + repr(str(CONTROL / "packet") + ":/opt/sentinel-stack/HUGSIM")
        + ",OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')\n"
        + "q=subprocess.run(["
        + repr(PYTHON)
        + ",'-'],input="
        + repr(body.encode())
        + ",env=env,capture_output=True,timeout=540)\nsys.stdout.buffer.write(q.stdout);sys.stderr.buffer.write(q.stderr);raise SystemExit(q.returncode)\n"
    )


def packet(root, source):
    inputs = read(root / BASE / "INPUTS.json")
    paths = set(inputs["files"])
    paths.update(
        BASE + "/" + name
        for name in ("INPUTS.json", "QUALIFICATION.json", "HYPOTHESIS.md", "GPU_BINDING.md")
    )
    records = {}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        values = {}
        for name in sorted(paths):
            data = subprocess.check_output(["git", "show", source + ":" + name], cwd=root)
            if data != (root / name).read_bytes():
                raise ValueError("source_not_frozen:" + name)
            values["packet/" + name] = data
        for name, path, key in (
            (
                "asset_inventory.json",
                "experiments/iter145_constrained_execution/proof/resume_complete_asset_report.json",
                "inventory",
            ),
            (
                "map_inventory.json",
                "experiments/iter145_constrained_execution/proof/resume_full_map_report.json",
                "map_inventory",
            ),
        ):
            data = subprocess.check_output(["git", "show", source + ":" + path], cwd=root)
            values[name] = json.dumps(json.loads(data)[key]).encode()
        for name, data in values.items():
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
            from hashlib import sha256

            records[name] = dict(bytes=len(data), sha256=sha256(data).hexdigest())
    if sum(v["bytes"] for v in records.values()) > 32 * 1024**2:
        raise ValueError("packet_cap")
    raw = buffer.getvalue()
    return raw, dict(
        commit=source, files=records, packet_sha256=sha256(raw).hexdigest(), packet_bytes=len(raw)
    )


def commit(root, paths, message):
    root = Path(root).resolve()
    evidence = root / BASE / "proof"
    for path in paths:
        path = Path(path)
        if not path.is_absolute():
            path = root / path
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(evidence):
            raise ValueError("non_evidence_commit_scope")
        if path.is_dir() and any(p.is_symlink() for p in path.rglob("*")):
            raise ValueError("evidence_symlink")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root).returncode:
        raise ValueError("unexpected_staged_work")
    subprocess.run(["git", "add", "--", *map(str, paths)], cwd=root, check=True)
    # Captured source is immutable evidence, including its original whitespace.
    # Source/style validation is performed on authored code before source freeze.
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def provider_shape(value):
    accelerators = value.get("guestAccelerators", [])
    if (
        str(value.get("id")) != VM_ID
        or not value.get("machineType", "").endswith("/g2-standard-8")
        or len(accelerators) != 1
        or accelerators[0].get("acceleratorCount") != 1
        or not accelerators[0].get("acceleratorType", "").endswith("/nvidia-l4")
    ):
        raise ValueError("provider_shape")


def block_pairs(block):
    if type(block) is not int or block != 0:
        raise ValueError("execution_block")
    return range(1)


def execute(root, block, source):
    root = Path(root).resolve()
    base = root / BASE
    allowance = 3600
    proof = base / "proof" / "block_000"
    if type(block) is not int or block != 0:
        raise ValueError("execution_block")
    from .baseline import verify as verify_baseline

    verify_baseline(root)
    proof.mkdir(parents=True, exist_ok=False)
    document = validate_plan(read(base / "STUDY_PLAN.json"))
    qualification = basis(root)
    admissions = base / "proof/admissions"
    admissions.mkdir(exist_ok=True)
    receipts = [read(admissions / f"pair_{i:03d}.json") for i in range(min(block_pairs(block)))]
    history(document, receipts, min(block_pairs(block)))
    if block != 0 or shutil.disk_usage(root).free < 4 * 1024**3:
        raise ValueError("block_or_local_capacity")
    price = read(base / "proof/price_binding.json")
    if not 0 < price["hourly_usd"] <= 3:
        raise ValueError("price_bound")
    raw, packet_info = packet(root, source)
    record(proof / "source_packet.json", packet_info)
    cloud = Cloud(proof)
    before = cloud.identity("initial_identity")
    provider_shape(before)
    if str(before.get("id")) != VM_ID or before.get("status") != "TERMINATED":
        raise ValueError("initial_provider_state")
    began = time.monotonic()
    budget = dict(
        started_monotonic=began,
        deadline_monotonic=began + allowance,
        max_seconds=allowance,
        conservative_compute_usd=allowance * 3 / 3600,
    )
    record(proof / "budget.json", budget)
    with (proof / "watchdog.log").open("xb") as log:
        watcher = subprocess.Popen(
            [sys.executable, "-m", "experiments.iter150_cloud_observation.cloud", str(proof)],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    token = uuid.uuid4().hex[:12]
    timer = f"sentinel163-block{block}-{token}.timer"
    owned = None
    deployed = False
    current_pair = None
    collected = set()
    report = dict(status="running", block=block, pairs=[])

    def call(label, data, code, timeout=90, runtime=True):
        return json.loads(
            cloud.ssh(label, rpc(data, code, runtime=runtime), timeout=timeout, owned=owned)
        )

    def collect(pair):
        binding = call(
            f"pair_{pair}_archive",
            dict(control=str(CONTROL), pair=pair),
            "from experiments.iter163_native_path_replay.collection import archive\nimport json\nprint(json.dumps(archive(payload['control'],payload['pair'])))\n",
            timeout=180,
        )
        local = proof / f"pair_{pair:03d}_raw.tar.gz"
        same_start(cloud.identity(f"pair_{pair}_download_before"), owned, running=True)
        q = cloud.run(
            f"pair_{pair}_download",
            [
                "gcloud",
                "compute",
                "scp",
                *CLOUD_ARGS,
                "--tunnel-through-iap",
                f"{VM}:{CONTROL}/pair_{pair:03d}_raw.tar.gz",
                str(local),
            ],
            timeout=180,
        )
        same_start(cloud.identity(f"pair_{pair}_download_after"), owned, running=True)
        if q.returncode:
            raise OSError("collection_download")
        if (
            sum(p.stat().st_size for p in proof.rglob("*") if p.is_file()) + binding["bytes"]
            > 512 * 1024**2
        ):
            raise ValueError("local_block_collection_cap")
        destination = base / "proof/study_raw" / f"pair_{pair:03d}"
        used = sum(p.stat().st_size for p in proof.rglob("*") if p.is_file())
        for prior in block_pairs(block):
            used += sum(
                p.stat().st_size
                for p in (base / "proof/study_raw" / f"pair_{prior:03d}").rglob("*")
                if p.is_file()
            )
        extract(local, destination, binding, remaining_bytes=512 * 1024**2 - used)
        record(proof / f"pair_{pair:03d}_collection.json", binding)
        collected.add(pair)
        return destination

    try:
        record(proof / "start_intent.json", dict(before=before, maximum_start_commands=1))
        cloud.run(
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
        owned = recover_start(cloud, proof, "owned_identity")
        if owned["status"] != "RUNNING":
            raise ValueError("start_not_running")
        record(proof / "owned.json", owned)
        for attempt in range(4):
            try:
                cloud.ssh(f"reachability_{attempt}", 'print("ready")\n', timeout=30, owned=owned)
                break
            except OSError:
                if attempt == 3:
                    raise
                time.sleep(3)
        duration = int(budget["deadline_monotonic"] - time.monotonic() - 120)
        setup = call(
            "host_setup",
            dict(control=str(CONTROL), timer=timer, seconds=duration, block=block),
            """import json,subprocess,shutil,time
from pathlib import Path
c=Path(payload['control'])
if payload['block']==0:c.mkdir(exist_ok=False)
else:assert c.is_dir() and not c.is_symlink()
assert shutil.disk_usage(c).free>=100*1024**3
q=subprocess.run(['systemd-run','--unit',payload['timer'].removesuffix('.timer'),'--on-active='+str(payload['seconds'])+'s','/sbin/shutdown','-h','now'],capture_output=True,text=True,timeout=15)
assert q.returncode==0,q.stderr
deadline=time.monotonic()+payload['seconds']
q=subprocess.run(['systemctl','show',payload['timer'],'--property=ActiveState,NextElapseUSecMonotonic'],capture_output=True,text=True,timeout=3)
assert q.returncode==0 and 'ActiveState=active' in q.stdout
print(json.dumps(dict(boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),timer_readback=q.stdout,deadline_monotonic=deadline,free_bytes=shutil.disk_usage(c).free)))
""",
            runtime=False,
        )
        environment = dict(
            vm_id=VM_ID,
            vm_start=owned["lastStartTimestamp"],
            host_boot=setup["boot"],
            host_deadline_id=timer,
        )
        if block == 0:
            upload = call(
                "extract_packet",
                dict(
                    control=str(CONTROL),
                    payload=base64.b64encode(raw).decode(),
                    records=packet_info["files"],
                ),
                """import base64,hashlib,io,json,tarfile
from pathlib import Path
c=Path(payload['control']);raw=base64.b64decode(payload['payload'])
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 members=archive.getmembers()
 assert {m.name for m in members}==set(payload['records']) and len(members)==len(payload['records'])
 assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
 assert sum(m.size for m in members)<32*1024**2
 for m in members:
  data=archive.extractfile(m).read();expected=payload['records'][m.name]
  assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256']
  p=c/m.name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(data)
print(json.dumps(dict(status='supported',files=len(members))))
""",
                timeout=120,
                runtime=False,
            )
            record(proof / "packet_extraction.json", upload)
            deployment = call(
                "prepare_runtime",
                dict(control=str(CONTROL), source=source),
                "from experiments.iter163_native_path_replay.remote_ops import prepare\nimport json\nprint(json.dumps(prepare(payload['control'],payload['source'])))\n",
                timeout=600,
            )
        else:
            deployment = call(
                "verify_runtime",
                dict(control=str(CONTROL), source=source),
                "from pathlib import Path\nimport json\nfrom experiments.iter163_native_path_replay.records import read\nfrom experiments.iter145_constrained_execution.gpu_batch import check_files\nc=Path(payload['control']);m=read(c/'execution_manifest.json');assert m['source_commit']==payload['source'];check_files(m);print(json.dumps(read(c/'deployment.json')))\n",
                timeout=600,
            )
        deployed = True
        record(proof / "deployment.json", deployment)
        envelope = dict(
            block=block,
            binding=environment,
            timer_unit=timer,
            timer_readback=setup["timer_readback"],
            deadline_monotonic=setup["deadline_monotonic"],
            pair_units={str(i): f"sentinel163-pair{i}-{token}.service" for i in block_pairs(block)},
        )
        result = call(
            "record_envelope",
            dict(control=str(CONTROL), envelope=envelope),
            "from pathlib import Path\nimport json\nfrom experiments.iter163_native_path_replay.records import record\ne=payload['envelope'];record(Path(payload['control'])/('block_%03d_envelope.json'%e['block']),e);print(json.dumps(e))\n",
        )
        record(proof / "envelope.json", result)
        if block == 0:
            qualified = call(
                "qualify_active_owner",
                dict(control=str(CONTROL), environment=environment, token=token),
                "from pathlib import Path\nimport json\nfrom experiments.iter163_native_path_replay.records import read\nfrom experiments.iter163_native_path_replay.qualify_host import qualify\nc=Path(payload['control']);print(json.dumps(qualify(c/'ownership_fixture',read(c/'plan.json'),payload['environment'],payload['token'])))\n",
                timeout=120,
            )
            if qualified["status"] != "supported":
                raise ValueError("host_qualification")
            record(proof / "host_qualification.json", qualified)
        for pair in block_pairs(block):
            current_pair = pair
            if shutil.disk_usage(root).free < 4 * 1024**3:
                raise ValueError("local_collection_reserve")
            remaining(budget["deadline_monotonic"], time.monotonic())
            history(document, receipts, pair)
            for i in range(pair):
                from experiments.iter148_recovery_study.admission import committed_file

                committed_file(
                    root,
                    subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=root, text=True
                    ).strip(),
                    admissions / f"pair_{i:03d}.json",
                )
            permit = dict(
                status="supported",
                pair=pair,
                block=block,
                plan_sha256=PLAN,
                manifest_sha256=deployment["manifest_sha256"],
                qualification_sha256=qualification,
                history=receipts,
                envelope_sha256=identity(envelope),
            )
            # Launch is invoked once. A missing reply enters read-only reconciliation below.
            try:
                launched = call(
                    f"pair_{pair}_launch",
                    dict(control=str(CONTROL), permit=permit),
                    "import json\nfrom experiments.iter163_native_path_replay.remote_ops import launch\nprint(json.dumps(launch(payload['control'],payload['permit'])))\n",
                )
                record(proof / f"pair_{pair:03d}_launch.json", launched)
            except OSError as exc:
                record(
                    proof / f"pair_{pair:03d}_launch_reply_unavailable.json",
                    dict(error=repr(exc), launch_retry=False),
                )
            expected = None
            for attempt in range(4):
                try:
                    expected = call(
                        f"pair_{pair}_attach_{attempt}",
                        dict(control=str(CONTROL), pair=pair, environment=environment),
                        "import json\nfrom experiments.iter150_cloud_observation.native import bind\nprint(json.dumps(bind(payload['control'],payload['pair'],payload['environment'])[0]))\n",
                    )
                    break
                except OSError:
                    if attempt == 3:
                        raise
                    time.sleep(2**attempt)
            record(proof / f"pair_{pair:03d}_binding.json", expected)
            count = [0]

            def observer(request, timeout):
                index = count[0]
                count[0] += 1
                value = call(
                    f"pair_{pair}_observe_{index}",
                    dict(
                        control=str(CONTROL),
                        pair=pair,
                        expected=expected,
                        request=request,
                        envelope=envelope,
                    ),
                    "import json\nfrom experiments.iter163_native_path_replay.ownership import observation\nprint(json.dumps(observation(payload['control'],payload['pair'],payload['expected'],payload['request'],payload['envelope'])))\n",
                    timeout=timeout,
                )
                print(
                    json.dumps(
                        dict(pair=pair, observation=index, reply_bytes=len(value["raw_hex"]) // 2)
                    ),
                    flush=True,
                )
                return bytes.fromhex(value["raw_hex"]), {
                    k: bytes.fromhex(v) for k, v in value["blobs_hex"].items()
                }

            limits = Limits(
                deadline=min(time.monotonic() + 2600, budget["deadline_monotonic"] - 300),
                max_reads=125,
                max_unavailable=4,
                read_timeout=60,
                poll_seconds=20,
                backoff=(2, 4, 8),
            )
            trace = reconcile(
                expected,
                limits,
                f"native163-{block}-{pair}",
                observer,
                time.monotonic,
                time.sleep,
            )
            record(proof / f"pair_{pair:03d}_trace.json", trace)
            check(trace)
            if not trace["worker_complete"]:
                raise ValueError("pair_observation:" + trace["reason"])
            destination = collect(pair)
            raw_commit = commit(
                root,
                [proof, destination],
                f"iter163: retain pair {pair} raw before scientific replay",
            )
            report["pairs"].append(dict(pair=pair, status="raw_retained", raw_commit=raw_commit))
            print(json.dumps(report["pairs"][-1]), flush=True)
        report["status"] = "supported"
    except Exception as exc:
        report.update(status="failed", error=repr(exc), traceback=traceback.format_exc())
        print(json.dumps(dict(status="failed", error=repr(exc))), flush=True)
        if deployed and current_pair is not None and current_pair not in collected:
            try:
                # Stop only this unique launched service, within the verified owned VM start.
                call(
                    "failure_stop_service",
                    dict(unit=envelope["pair_units"][str(current_pair)]),
                    "import json,subprocess\nq=subprocess.run(['systemctl','stop',payload['unit']],capture_output=True,text=True,timeout=30);print(json.dumps(dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr)))\n",
                    timeout=60,
                    runtime=False,
                )
                cleanup = call(
                    "failure_cleanup_client",
                    dict(
                        ids=[
                            s["id"]
                            for s in document["slots"][current_pair * 2 : current_pair * 2 + 2]
                        ]
                    ),
                    "import json,subprocess\nfrom experiments.iter147_full_horizon_execution.gpu import CONTAINER,cleanup_client\nq=subprocess.run(['docker','inspect',CONTAINER,'--format','{{index .Config.Labels \"sentinel.iter147.episode\"}}'],capture_output=True,text=True,timeout=10)\nif q.returncode==0:\n assert q.stdout.strip() in payload['ids'];r=cleanup_client(q.stdout.strip())\nelse:r=cleanup_client(payload['ids'][0])\nprint(json.dumps(r))\n",
                    timeout=90,
                )
                record(proof / "failure_cleanup.json", cleanup)
                collect(current_pair)
            except Exception as recovery_error:
                report["partial_collection_error"] = repr(recovery_error)
    finally:
        if deployed:
            try:
                post = call(
                    "postflight",
                    dict(control=str(CONTROL)),
                    "import json\nfrom experiments.iter163_native_path_replay.remote_ops import postflight\nprint(json.dumps(postflight(payload['control'])))\n",
                    timeout=360,
                )
                record(proof / "postflight.json", post)
                if post["status"] != "supported":
                    report["status"] = "failed"
            except Exception as exc:
                report.update(status="failed", postflight_error=repr(exc))
        try:
            if owned is None:
                from .startup import denied_start

                first = cloud.identity("closure_reconcile")
                try:
                    closure = denied_start(
                        before,
                        read(proof / "commands/start.json")["returncode"],
                        (proof / "commands/start.stderr").read_text(),
                        [first, cloud.identity("closure_denied_confirmation")],
                    )
                except ValueError:
                    owned = recover_start(cloud, proof, "closure_owned_reconcile")
                else:
                    record(proof / "closure.json", closure)
                    report.update(
                        termination_verified=True,
                        new_start_observed=False,
                        scientific_slots_initialized=0,
                        lifecycle="start_denied_capacity",
                    )
            if owned is not None:
                final = cloud.stop("closure", owned)
                record(proof / "closure.json", dict(status="supported", instance=final))
                report["termination_verified"] = True
        except Exception as exc:
            report.update(status="failed", termination_verified=False, closure_error=repr(exc))
        try:
            report["watchdog_exit"] = watcher.wait(timeout=10)
        except subprocess.TimeoutExpired:
            report["watchdog_exit"] = None
        elapsed = time.monotonic() - began
        report.update(elapsed_seconds=elapsed, conservative_compute_usd=elapsed * 3 / 3600)
        report["within_registered_budget"] = elapsed <= allowance
        if report["watchdog_exit"] != 0 or not report["within_registered_budget"]:
            report["status"] = "failed"
        record(proof / "result.json", report)
        print(json.dumps(report), flush=True)
    # Scientific replay runs only after verified host closure; it cannot consume GPU budget.
    if report["status"] == "supported" and report.get("termination_verified"):
        from .replay import admit

        for retained in report["pairs"]:
            pair = retained["pair"]
            destination = base / "proof/study_raw" / f"pair_{pair:03d}"
            try:
                receipt = admit(
                    root,
                    destination,
                    document,
                    pair,
                    retained["raw_commit"],
                    [],
                    base / "proof/study_raw",
                )
            except Exception as exc:
                receipt = dict(
                    status="invalid",
                    pair=pair,
                    raw_commit=retained["raw_commit"],
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )
            record(admissions / f"pair_{pair:03d}.json", receipt)
            commit(
                root,
                [admissions / f"pair_{pair:03d}.json"],
                f"iter163: retain independent admission for pair {pair}",
            )
            print(
                json.dumps(
                    dict(
                        admission=receipt["status"],
                        scientific_status=receipt.get("scientific_status"),
                    )
                ),
                flush=True,
            )
            if receipt["status"] != "supported":
                return 1
    return 0 if report["status"] == "supported" and report.get("termination_verified") else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--block", type=int, choices=(0,), required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    raise SystemExit(execute(Path.cwd(), args.block, args.source))
