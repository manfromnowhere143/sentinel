"""Bounded immutable stage records and frozen-source bindings."""

import json
import platform
import shutil
import sys
import time

from .common import BASE, encode, git, read, require, rss, sha, source_check, write


def initialize(root, output, source, stage):
    plan = json.loads(read(root, BASE / "PLAN.json"))
    source_check(root, plan, source)
    git(root, "merge-base", "--is-ancestor", source, "HEAD")
    require(output == root / BASE / "proof" / (stage + "_raw"), "stage_output")
    require(shutil.disk_usage(root).free >= plan["minimum_free_bytes"], "disk_budget")
    output.parent.mkdir(exist_ok=True)
    output.mkdir(exist_ok=False)
    write(
        output / "initialized.json",
        dict(
            stage=stage,
            source_commit=source,
            plan_sha256=sha(encode(plan)),
            python=sys.version,
            platform=platform.platform(),
        ),
    )
    return plan


def committed(root, raw, commit, plan):
    relative = raw.relative_to(root).as_posix()
    names = git(root, "ls-tree", "-r", "--name-only", commit, "--", relative).decode().splitlines()
    require(
        set(names) == {p.relative_to(root).as_posix() for p in raw.rglob("*") if p.is_file()},
        "raw_inventory",
    )
    total = 0
    for name in names:
        data = read(root, name)
        total += len(data)
        require(git(root, "show", commit + ":" + name) == data, "raw_not_committed")
    require(total <= plan["max_output_bytes"], "output_budget")
    execution = json.loads(read(raw, "execution.json"))
    initialized = json.loads(read(raw, "initialized.json"))
    source = execution["source_commit"]
    source_check(root, plan, source)
    git(root, "merge-base", "--is-ancestor", source, commit)
    require(
        execution["status"] == "completed"
        and execution["new_driving_episodes"] == execution["provider_spend"] == 0,
        "execution_scope",
    )
    require(
        execution["stage"] == initialized["stage"]
        and source == initialized["source_commit"]
        and execution["plan_sha256"] == initialized["plan_sha256"] == sha(encode(plan)),
        "initialization_identity",
    )
    require(
        0 < execution["elapsed_seconds"] <= plan[execution["stage"] + "_producer_seconds"],
        "producer_time",
    )
    require(0 < execution["peak_rss_bytes"] <= plan["max_rss_bytes"], "producer_memory")
    return execution


def finish(output, source, plan, stage, started, **details):
    elapsed = time.monotonic() - started
    total = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
    require(total < plan["max_output_bytes"] - 100000, "output_budget")
    require(elapsed <= plan[stage + "_producer_seconds"], "producer_deadline")
    require(rss() <= plan["max_rss_bytes"], "memory_budget")
    write(
        output / "execution.json",
        dict(
            status="completed",
            stage=stage,
            source_commit=source,
            plan_sha256=sha(encode(plan)),
            elapsed_seconds=elapsed,
            peak_rss_bytes=rss(),
            raw_bytes_before_finalization=total,
            new_driving_episodes=0,
            provider_spend=0,
            **details,
        ),
    )


def failure(output, started, exc):
    write(
        output / "failure.json",
        dict(
            status="invalid",
            error=f"{type(exc).__name__}:{exc}",
            elapsed_seconds=time.monotonic() - started,
        ),
    )
