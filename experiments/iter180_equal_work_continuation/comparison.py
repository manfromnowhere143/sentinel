"""Paired finite-population contrasts without treating censoring as failure."""

from .common import require


def compare(records):
    require(
        all(type(r["witness"]) is bool and type(r["censored"]) is bool for r in records),
        "paired_types",
    )
    require(all(not (r["witness"] and r["censored"]) for r in records), "witness_censor_conflict")
    roots = list(dict.fromkeys(r["call"] for r in records))
    require(len(roots) == 16 and len(records) == 32, "paired_population")
    pairs = []
    for call in roots:
        arms = {r["arm"]: r for r in records if r["call"] == call}
        require(set(arms) == {"program", "beam"}, "paired_arms")
        values = {a: None if r["censored"] else r["witness"] for a, r in arms.items()}
        if any(v is None for v in values.values()):
            kind = "unresolved_censoring"
        else:
            kind = (
                ("both_witness" if values["program"] else "gain")
                if values["beam"]
                else ("loss" if values["program"] else "both_miss")
            )
        pairs.append(dict(call=call, **values, classification=kind))
    counts = {
        k: sum(p["classification"] == k for p in pairs)
        for k in ("gain", "loss", "both_witness", "both_miss", "unresolved_censoring")
    }
    status = (
        "contradicted"
        if counts["loss"]
        else (
            "inconclusive"
            if counts["unresolved_censoring"]
            else ("supported" if counts["gain"] else "null")
        )
    )
    return dict(
        status=status,
        pairs=pairs,
        gains=counts["gain"],
        losses=counts["loss"],
        both_witness=counts["both_witness"],
        both_miss=counts["both_miss"],
        censored_pairs=counts["unresolved_censoring"],
    )
