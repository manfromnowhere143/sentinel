#!/usr/bin/env python3
"""Extract the frozen donor brake schedules for the iteration 134 placebo arm.

Reads ONLY the committed released-union decision log from the power run and emits, for every
(class, seq, run) target, the donor episode's brake frame indices. The donor rule is frozen in
HYPOTHESIS.md:

    donor pair index q = (p + 1) mod len(class)
    donor run j        = (i + 1) mod 20

which excludes the target pair and the target seed by construction, and is a bijection on
(pair, run) within each class, so the placebo's scheduled brake budget equals the released
union's brake budget exactly at class level and in total.

Frame indexing (frozen): frame k is the k-th frame row (a row carrying "ts") after a "reset" row
within a block, zero-based. Frame k is a brake frame if and only if a "brake" row occurs between
frame row k and frame row k + 1.

Block mapping (frozen, verified against the log): the run index cycles 0..19 per pair, so block b
maps to PAIR_ORDER[b // 20] and run b % 20.

Usage: extract_donor_schedules.py <out.json> <union_log_part> [<union_log_part> ...]
"""
import gzip
import hashlib
import json
import subprocess
import sys

CLASS_SEQS = {
    "stationary": ["0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"],
    "frontal": ["0103", "0106", "0110", "0346", "0923"],
    "side": ["0103", "0108", "0110", "0278", "0921"],
}
CLASSES = ["stationary", "frontal", "side"]
PAIR_ORDER = [(c, s) for c in CLASSES for s in CLASS_SEQS[c]]
RUNS = 20
EXPECTED_BLOCKS = len(PAIR_ORDER) * RUNS

SCHEMA = "iter134.donor_schedules.v1"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_blocks(parts):
    """Return blocks in log order: list of {"frames": int, "brake_frames": [int]}."""
    raw = subprocess.run(["cat", *parts], check=True, stdout=subprocess.PIPE).stdout
    text = gzip.decompress(raw).decode("utf-8", errors="replace")
    blocks = []
    cur = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("reset"):
            cur = {"frames": 0, "brake_frames": [], "log_run": row.get("run")}
            blocks.append(cur)
        elif cur is None:
            continue
        elif "ts" in row:
            cur["frames"] += 1
        elif row.get("brake"):
            # the brake row for frame k is emitted after frame row k
            k = cur["frames"] - 1
            if k >= 0 and (not cur["brake_frames"] or cur["brake_frames"][-1] != k):
                cur["brake_frames"].append(k)
    return blocks


def main():
    out_path, *parts = sys.argv[1:]
    blocks = read_blocks(parts)
    problems = []
    if len(blocks) != EXPECTED_BLOCKS:
        problems.append(f"block-count:{len(blocks)}!={EXPECTED_BLOCKS}")

    # committed union episodes keyed by (class, seq, run)
    union = {}
    for b, blk in enumerate(blocks):
        cls, seq = PAIR_ORDER[b // RUNS]
        run = b % RUNS
        if blk.get("log_run") != run:
            problems.append(f"run-index-mismatch:{cls}/{seq}/{run}:log={blk.get('log_run')}")
        union[(cls, seq, run)] = blk

    schedules = {}
    total_scheduled = 0
    per_class_scheduled = dict.fromkeys(CLASSES, 0)
    per_class_union = dict.fromkeys(CLASSES, 0)
    for cls in CLASSES:
        seqs = CLASS_SEQS[cls]
        for p, seq in enumerate(seqs):
            for i in range(RUNS):
                q = (p + 1) % len(seqs)
                j = (i + 1) % RUNS
                donor_seq = seqs[q]
                if donor_seq == seq:
                    problems.append(f"donor-pair-not-excluded:{cls}/{seq}/{i}")
                if j == i:
                    problems.append(f"donor-seed-not-excluded:{cls}/{seq}/{i}")
                donor = union.get((cls, donor_seq, j))
                if donor is None:
                    problems.append(f"donor-missing:{cls}/{donor_seq}/{j}")
                    continue
                key = f"{cls}/{seq}/{i}"
                schedules[key] = {
                    "target_class": cls,
                    "target_seq": seq,
                    "target_run": i,
                    "donor_class": cls,
                    "donor_seq": donor_seq,
                    "donor_run": j,
                    "donor_frame_count": donor["frames"],
                    "brake_frames": donor["brake_frames"],
                    "scheduled_brake_count": len(donor["brake_frames"]),
                }
                total_scheduled += len(donor["brake_frames"])
                per_class_scheduled[cls] += len(donor["brake_frames"])
                per_class_union[cls] += len(union[(cls, seq, i)]["brake_frames"])

    # the bijection guarantee: scheduled budget == union budget, per class and in total
    union_total = sum(len(b["brake_frames"]) for b in union.values())
    if total_scheduled != union_total:
        problems.append(f"budget-not-matched:{total_scheduled}!={union_total}")
    for cls in CLASSES:
        if per_class_scheduled[cls] != per_class_union[cls]:
            problems.append(f"class-budget-not-matched:{cls}")

    report = {
        "schema": SCHEMA,
        "verdict": "DONOR_SCHEDULES_OK" if not problems else "DONOR_SCHEDULES_INVALID",
        "source_log_parts": [{"path": p, "sha256": sha256_file(p)} for p in parts],
        "pair_order": [f"{c}/{s}" for c, s in PAIR_ORDER],
        "runs_per_pair": RUNS,
        "block_count": len(blocks),
        "target_count": len(schedules),
        "union_total_brake_frames": union_total,
        "scheduled_total_brake_frames": total_scheduled,
        "per_class_scheduled_brake_frames": per_class_scheduled,
        "per_class_union_brake_frames": per_class_union,
        "donor_rule": "q=(p+1)%len(class); j=(i+1)%20",
        "problem_count": len(problems),
        "problems": problems,
        "schedules": schedules,
    }
    with open(out_path, "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    print(f"{report['verdict']} blocks={len(blocks)} targets={len(schedules)} "
          f"scheduled={total_scheduled} union={union_total} problems={len(problems)}")
    for p in problems[:10]:
        print("  problem:", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
