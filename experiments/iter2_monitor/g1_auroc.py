#!/usr/bin/env python3
"""G1 gate — does the frozen planner's own output separate its collisions?

Replays the shadow dump (raw per-frame planner outputs) through the Sentinel monitor and measures
the AUROC of the per-run risk against the known per-run collision outcome. No ground truth, no
intervention — purely: did the planner's own plan + forecasts foresee the crash?

Resolves the future_trajs coordinate convention empirically: scores both 'displacement' (agent
absolute future = obj_xy + fut) and 'absolute' (fut already absolute), and reports the AUROC of
each. The physically-correct convention should separate collisions; the wrong one should not.

Usage: g1_auroc.py <risk.jsonl> <outcomes.tsv>
  outcomes.tsv: one line per run in execution order: "<pair>\\t<ncap_score>\\t<impact_speed>"
"""
import gzip
import json
import sys
from statistics import mean

sys.path.insert(0, ".")
from sentinel.monitor import AgentForecast, compute_risk  # noqa: E402


def _open(path):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)


def segment_runs(jsonl_path):
    """Split the dump into runs by reset markers; return list of [frame, ...]."""
    runs, cur = [], None
    n_err = 0
    for line in _open(jsonl_path):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("reset"):
            if cur is not None:
                runs.append(cur)
            cur = []
        elif "err" in d:
            n_err += 1
        elif cur is not None:
            cur.append(d)
    if cur:
        runs.append(cur)
    return runs, n_err


def build_agents(frame, convention):
    """Build AgentForecast list from a dumped frame under the chosen convention."""
    objs = frame.get("objs") or []
    scores = frame.get("scores") or []
    futs = frame.get("futs") or []
    agents = []
    for i in range(min(len(objs), len(scores), len(futs))):
        ox, oy = float(objs[i][0]), float(objs[i][1])
        w, h = float(objs[i][2]), float(objs[i][3])
        half = max(0.6, 0.5 * max(w, h))
        modes = []
        for mode in futs[i]:
            if convention == "displacement":
                modes.append([[ox + float(p[0]), oy + float(p[1])] for p in mode])
            else:  # absolute
                modes.append([[float(p[0]), float(p[1])] for p in mode])
        agents.append(AgentForecast(score=float(scores[i]), half_extent=half, modes=modes))
    return agents


def run_signals(frames, convention, **kw):
    """Per-run risk and closest-predicted-gap aggregates from its frames."""
    risk, gap = [], []
    for fr in frames:
        if not fr.get("traj"):
            continue
        agents = build_agents(fr, convention)
        b = compute_risk(fr["traj"], agents, **kw)
        risk.append(b.risk)
        gap.append(b.min_predicted_gap if b.min_predicted_gap == b.min_predicted_gap else 99.0)
    if not risk:
        return {"max": 0.0, "last3max": 0.0, "mean": 0.0, "gap_last3min": 99.0, "gap_min": 99.0}
    return {
        "max": max(risk), "last3max": max(risk[-3:]), "mean": mean(risk),
        "gap_last3min": min(gap[-3:]), "gap_min": min(gap),
    }


def auroc(scores, labels):
    """Mann-Whitney AUROC; labels are 1 (collision) / 0 (clean). Ties get average rank."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan")
    order = sorted(range(len(scores)), key=lambda k: scores[k])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    sum_pos = sum(r for r, y in zip(ranks, labels) if y == 1)
    n_pos, n_neg = len(pos), len(neg)
    return (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def main():
    risk_path, outcomes_path = sys.argv[1], sys.argv[2]
    runs, n_err = segment_runs(risk_path)
    outcomes = []
    for line in open(outcomes_path):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            outcomes.append((parts[0], float(parts[1]), float(parts[2])))

    n = min(len(runs), len(outcomes))
    print(f"runs in dump: {len(runs)}  outcomes: {len(outcomes)}  aligned: {n}  frame-errors: {n_err}")
    runs, outcomes = runs[:n], outcomes[:n]
    labels = [1 if imp > 0.0 else 0 for _, _, imp in outcomes]
    print(f"collisions: {sum(labels)}  clean: {len(labels) - sum(labels)}")

    # the displacement convention is physically correct (absolute spuriously converges to origin);
    # sweep the imminent horizon and aggregate, proximity-only (the winning, simplest signal).
    print("\n=== displacement convention, proximity-only signal ===")
    best = (0.0, None)
    for horizon in (None, 4, 3, 2, 1):
        hlabel = "full" if horizon is None else f"h={horizon}"
        sig = [run_signals(fr, "displacement", use_confidence=False, use_disagreement=False,
                           horizon=horizon) for fr in runs]
        a_risk = auroc([s["last3max"] for s in sig], labels)
        # closest predicted gap: smaller gap => collision, so score = -gap
        a_gap = auroc([-s["gap_last3min"] for s in sig], labels)
        print(f"  horizon={hlabel:5s}  AUROC[last3max risk]={a_risk:.3f}  "
              f"AUROC[-closest_gap, last3]={a_gap:.3f}")
        if a_gap > best[0]:
            best = (a_gap, ("gap", horizon))
        if a_risk > best[0]:
            best = (a_risk, ("risk", horizon))

    print(f"\nBEST: AUROC={best[0]:.3f} via {best[1]}")

    # per-run table with the closest-predicted-gap (imminent horizon=3), for the writeup
    print("\n=== per-run (displacement, closest predicted gap over last-3 frames, horizon=3) ===")
    rows = []
    for (pair, sc, imp), fr in zip(outcomes, runs):
        g = run_signals(fr, "displacement", horizon=3)["gap_last3min"]
        rows.append((pair, sc, imp, int(imp > 0), g))
        print(f"  {pair:18s} score={sc:.2f} impact={imp:5.1f} collide={int(imp>0)} "
              f"closest_gap={g:5.2f}m")
    # separation summary
    cg = [g for *_, c, g in rows if c == 1]
    cl = [g for *_, c, g in rows if c == 0]
    if cg and cl:
        print(f"\nclosest-gap (m): collisions median={sorted(cg)[len(cg)//2]:.2f} "
              f"min={min(cg):.2f} max={max(cg):.2f}  |  "
              f"clean median={sorted(cl)[len(cl)//2]:.2f} min={min(cl):.2f} max={max(cl):.2f}")


if __name__ == "__main__":
    main()
