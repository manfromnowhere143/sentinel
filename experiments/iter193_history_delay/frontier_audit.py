"""One exploratory branch materialization and separate scalar-path admission."""

import argparse
import json
from pathlib import Path
import time
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter191_stop_wait_release.runtime import verify
from .clock import join
from .common import BASE, git, load_source, read, require, rss, sha, write, source_check

SOURCE = BASE / "proof/search_raw/origin_25_delay_0"
OUTPUT = BASE / "proof/frontier_audit_raw"
RAW_COMMIT = "a3f66a4424a679772705298ae5aaf2337ab4b037"


def bind_primary(root):
    name = str(BASE / "proof/admission.json")
    data = read(root, name)
    require(
        data == git(root, "show", "c5bb87b7e8d966750f875b13e381ac4ab651c16e:" + name),
        "primary_admission_changed",
    )
    primary = json.loads(data)
    source_check(root, json.loads(read(root, BASE / "PLAN.json")), primary["source_commit"])


def selected(sequences):
    require(bool(sequences), "empty_frontier")
    return min(
        sequences.values(),
        key=lambda s: (-s["trace"][-1]["route"]["rc"], s["trace"][-1]["frame"], s["node"]),
    )["node"]


def reconstruct(sequences, node):
    by_node = {s["node"]: s for s in sequences.values()}
    require(len(by_node) == len(sequences), "duplicate_node")
    pieces, seen = [], set()
    while node != 1:
        require(node in by_node and node not in seen, "missing_or_cyclic_ancestry")
        seen.add(node)
        part = by_node[node]
        require(part["parent"] < node, "native_order")
        pieces.append(part["trace"])
        node = part["parent"]
    trace = []
    for part in reversed(pieces):
        require(
            not trace
            or (trace[-1]["state"], trace[-1]["frame"]) == (part[0]["state"], part[0]["frame"]),
            "branch_join",
        )
        trace.extend(part if not trace else part[1:])
    require(bool(trace), "empty_branch")
    return trace


def original(root):
    for name in ("prefix.json", "sequences.json", "events.jsonl"):
        path = (SOURCE / name).as_posix()
        require(
            read(root, path) == git(root, "show", RAW_COMMIT + ":" + path), "original_raw_changed"
        )
    return json.loads(read(root, SOURCE / "prefix.json")), json.loads(
        read(root, SOURCE / "sequences.json")
    )


def acquire(root, source):
    started = time.monotonic()
    bind_primary(root)
    verify(root)
    for name in (
        BASE / "frontier_audit.py",
        BASE / "FRONTIER_AUDIT.md",
        Path("tests/test_iter193_frontier_audit.py"),
    ):
        require(
            read(root, name) == git(root, "show", source + ":" + name.as_posix()),
            "audit_source_changed",
        )
    case, _, history = load_source(root)
    prefix, sequences = original(root)
    require(prefix == history, "first_fire_history")
    node = selected(sequences)
    trace = join(prefix, reconstruct(sequences, node))
    folder = root / OUTPUT
    folder.mkdir(exist_ok=False)
    retain_trace(folder / "path", trace, query_for(case))
    require(time.monotonic() - started <= 300 and rss() <= 1073741824, "audit_producer_resources")
    write(
        folder / "execution.json",
        dict(
            status="completed",
            selected_node=node,
            source_commit=source,
            primary_raw_commit=RAW_COMMIT,
            materialization_queries=len(trace),
            elapsed_seconds=time.monotonic() - started,
            peak_rss_bytes=rss(),
        ),
    )


def check(root, raw_commit):
    started = time.monotonic()
    bind_primary(root)
    verify(root)
    folder = root / OUTPUT
    paths = (
        git(root, "ls-tree", "-r", "--name-only", raw_commit, "--", str(OUTPUT))
        .decode()
        .splitlines()
    )
    require(
        set(paths) == {p.relative_to(root).as_posix() for p in folder.rglob("*") if p.is_file()},
        "audit_raw_inventory",
    )
    total = 0
    for path in paths:
        data = read(root, path)
        total += len(data)
        require(data == git(root, "show", raw_commit + ":" + path), "audit_raw_changed")
    require(total <= 32 * 1024 * 1024, "audit_output_cap")
    execution = json.loads(read(folder, "execution.json"))
    require(
        execution["status"] == "completed" and execution["primary_raw_commit"] == RAW_COMMIT,
        "audit_execution_identity",
    )
    for name in (
        BASE / "frontier_audit.py",
        BASE / "FRONTIER_AUDIT.md",
        Path("tests/test_iter193_frontier_audit.py"),
    ):
        require(
            read(root, name)
            == git(root, "show", execution["source_commit"] + ":" + name.as_posix()),
            "audit_source_changed",
        )
    require(
        0 < execution["elapsed_seconds"] <= 300 and 0 < execution["peak_rss_bytes"] <= 1073741824,
        "audit_producer_resources",
    )
    case, old, history = load_source(root)
    prefix, sequences = original(root)
    require(prefix == history, "audit_history")
    nodes = {}
    for line in read(root, SOURCE / "events.jsonl").splitlines():
        event = json.loads(line)
        if event["kind"] == "native_event" and event["event"]["kind"] in (1, 2):
            event = event["event"]
            nodes[event["node"]] = event
    ordered = sorted(
        nodes,
        key=lambda n: (
            -outcome(nodes[n]["state"][:5], case["geometry"])["rc"],
            nodes[n]["state"][5],
            n,
        ),
    )
    node = execution["selected_node"]
    require(node == ordered[0], "audit_selection")
    parts = []
    while node != 1:
        event = nodes[node]
        sequence = sequences[str(event["token"])]
        require(
            sequence["node"] == node and sequence["parent"] == event["parent"], "audit_ancestry"
        )
        parts.insert(0, sequence["trace"][1:])
        node = event["parent"]
    expected = history[:]
    for part in parts:
        for row in part:
            absolute = row["frame"] + 25
            expected.append(dict(row, id=absolute, parent=absolute - 1, frame=absolute))
    trace = json.loads(read(folder / "path", "trace.json"))
    require(trace == expected and execution["materialization_queries"] == len(trace), "audit_join")
    complete = trace[-1]["route"]["rc"] >= 1
    metrics = verify_path(
        trace,
        case["geometry"],
        old,
        case["points"],
        case["ground"],
        lambda i: read(folder / "path", f"mask_{i:03d}.bin", 40000),
        complete,
        started + 900,
    )
    require(time.monotonic() - started <= 900 and rss() <= 1073741824, "audit_checker_resources")
    result = dict(
        status="supported",
        analysis="exploratory post-admission branch replay",
        raw_commit=raw_commit,
        source_commit=execution["source_commit"],
        primary_raw_commit=RAW_COMMIT,
        selected_node=execution["selected_node"],
        complete=complete,
        final_frame=trace[-1]["frame"],
        progress=trace[-1]["route"]["rc"],
        scalar_classifications=len(trace) * len(case["points"]),
        **metrics,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        trace_sha256=sha(read(folder / "path", "trace.json")),
        boundary="Post-selected branch, not the expired planner's returned result, complete recovery, or executed online intervention.",
    )
    write(root / BASE / "proof/frontier_admission.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["acquire", "check"])
    p.add_argument("commit")
    a = p.parse_args()
    (acquire if a.stage == "acquire" else check)(Path.cwd(), a.commit)
