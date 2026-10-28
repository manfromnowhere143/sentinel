"""Post-admission descriptive tables only; no search, query or scientific retry."""

import json
from pathlib import Path
from .common import BASE, encode, read, sha


def derive(root):
    raw = read(root, BASE / "proof/admission.json")
    admission = json.loads(raw)
    rows = admission["records"]
    groups = []
    for kind in ("original", "goal"):
        for name in ("bend_left", "bend_right", "chicane_left", "chicane_right"):
            selected = [r for r in rows if r["kind"] == kind and r["case"] == name]
            arms = []
            for i, label in enumerate(("baseline", "candidate")):
                values = [r["arms"][i] for r in selected]
                arms.append(
                    dict(
                        arm=label,
                        complete=sum(v["complete"] for v in values),
                        attempts=sum(v["attempts"] for v in values),
                        queries=sum(v["queries"] for v in values),
                        primary_checkpoint_crossings=sum(
                            v["primary_checkpoint_crossings"] for v in values
                        ),
                        extra_checkpoint_crossings=sum(
                            v["extra_checkpoint_crossings"] for v in values
                        ),
                        max_original_plus_seconds=max(
                            (v["original_plus_seconds"] for v in values), default=None
                        ),
                    )
                )
            groups.append(
                dict(
                    kind=kind,
                    case=name,
                    requests=len(selected),
                    arms=arms,
                    gains=sum(
                        not r["arms"][0]["complete"] and r["arms"][1]["complete"] for r in selected
                    ),
                    losses=sum(
                        r["arms"][0]["complete"] and not r["arms"][1]["complete"] for r in selected
                    ),
                )
            )
    result = dict(
        admission_sha256=sha(raw),
        groups=groups,
        max_original_plus_seconds=max(a["original_plus_seconds"] for r in rows for a in r["arms"]),
        max_original_plus_attempts=max(
            a["original_plus_attempts"] for r in rows for a in r["arms"]
        ),
        candidate_feedback_requests=sum(r["arms"][1]["feedback_requests"] for r in rows),
    )
    (root / BASE / "proof/descriptive.json").write_bytes(encode(result))
    text = [
        "# Iter191 — every paired request",
        "",
        "Derived from independently admitted evidence. Each cell is baseline → candidate.",
        "Full completion requires the original remaining budget, including payload serialization.",
        "The 21 goal requests are synthetic; they are not original expansion requests.",
        "",
        "| Request | Complete | End frame | End progress | Attempts | Queries | Primary / extra checkpoint crossings | Original + seconds |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        a, b = row["arms"]
        text.append(
            f"| {row['id']} | {int(a['complete'])} → {int(b['complete'])} | "
            f"{a['returned_frame']} → {b['returned_frame']} | {a['returned_progress']:.6f} → {b['returned_progress']:.6f} | "
            f"{a['attempts']} → {b['attempts']} | {a['queries']} → {b['queries']} | "
            f"{a['primary_checkpoint_crossings']}/{a['extra_checkpoint_crossings']} → {b['primary_checkpoint_crossings']}/{b['extra_checkpoint_crossings']} | "
            f"{a['original_plus_seconds']:.6f} → {b['original_plus_seconds']:.6f} |"
        )
    text += [
        "",
        "Progress is the frozen sampled-route completion measure. Lower returned progress or higher cost remains visible even when full-completion counts improve.",
        "These are single exposed-request wall observations, not latency distributions or end-to-end response delay.",
        "Exact values and censoring fields: [admission](proof/admission.json).",
        "",
    ]
    (root / BASE / "PAIRS.md").write_text("\n".join(text))
    print(json.dumps(result))


if __name__ == "__main__":
    derive(Path.cwd())
