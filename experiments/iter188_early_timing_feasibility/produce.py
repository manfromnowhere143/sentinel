"""One prospective bound/probe pass; exclusive output and retained failure."""

import argparse
import json
from pathlib import Path
import shutil
import time

from .bound import certificate
from .contract import check_plan
from .common import BASE, GEOMETRY, OLD, encode, read, require, rss, sha, source_check, write
from .probes import actions, probe
from .runtime import verify


def acquire(root, source):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_plan(root, plan)
    source_check(root, source, plan)
    verify(root)
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "disk_budget")
    output = root / BASE / "proof/raw"
    output.mkdir(parents=True, exist_ok=False)
    write(output / "initialized.json", dict(source_commit=source, plan_sha256=sha(encode(plan))))
    try:
        population = json.loads(read(root, BASE / "POPULATION.json"))
        cases = {c["id"]: c["geometry"] for c in json.loads(read(root, GEOMETRY))}
        old = json.loads(read(root, OLD))
        count = probes = 0
        with (output / "records.jsonl").open("xb") as stream:
            for group in ("endpoints", "successful_transition_controls"):
                for item in population[group]:
                    require(time.monotonic() - started < plan["producer_seconds"] and rss() <= plan["max_rss_bytes"], "producer_resources")
                    geometry = cases[item["case"]]
                    bound = certificate(item["state"], item["frame"], geometry, old)
                    choices = actions(item["state"]) if group == "endpoints" else [item["next"]["action"]]
                    observed = [probe(item["state"], item["frame"], action, geometry, old) for action in choices]
                    stream.write(encode(dict(group=group, id=item["id"], certificate=bound, probes=observed)))
                    count += 1
                    probes += len(observed)
                    require(stream.tell() <= plan["max_output_bytes"] - 100000, "output_budget")
        verify(root)
        elapsed = time.monotonic() - started
        require(elapsed <= plan["producer_seconds"] and rss() <= plan["max_rss_bytes"], "producer_final_resources")
        write(output / "execution.json", dict(status="completed", source_commit=source,
              plan_sha256=sha(encode(plan)), records=count, scalar_probes=probes,
              elapsed_seconds=elapsed, peak_rss_bytes=rss(), new_driving_episodes=0,
              new_integrated_runs=0, background_queries=0, provider_spend=0))
    except Exception as exc:
        write(output / "failure.json", dict(status="invalid", error=f"{type(exc).__name__}:{exc}", elapsed_seconds=time.monotonic() - started))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    acquire(Path.cwd(), args.source)
