"""Apply a frozen clock-only Iteration-135 braking schedule to UniAD's returned trajectory."""

import subprocess


SRV = "/opt/sentinel-stack/UniAD/inference/server.py"
subprocess.run(
    ["git", "-C", "/opt/sentinel-stack/UniAD", "checkout", "--", "inference/server.py"],
    check=True,
)
src = open(SRV).read()

HELPERS = '''
# ---- Sentinel iter135: frozen blind-dose policy -----------------------------------------------
import json as _sjson, os as _sos
_SENTINEL_LOG = _sos.environ.get("SENTINEL_LOG", "/model/sentinel_i135_blind.jsonl")
_SENTINEL_SCHED_PATH = _sos.environ.get(
    "SENTINEL_DOSE_SCHEDULE", "/model/dose_schedules.json"
)
_SENTINEL_PAIR = _sos.environ.get("SENTINEL_DOSE_PAIR", "")
_SENTINEL_DOSE = _sos.environ.get("SENTINEL_DOSE_ID", "")
_SENTINEL_CLASS, _SENTINEL_SEQUENCE = _SENTINEL_PAIR.split("/", 1)
with open(_SENTINEL_SCHED_PATH) as _sf:
    _SENTINEL_DOCUMENT = _sjson.load(_sf)
_SENTINEL_SCHEDULES = _SENTINEL_DOCUMENT["schedules"]
_sentinel_run = {"i": -1, "k": 0, "frames": None, "key": None}


def _sentinel_write(row):
    with open(_SENTINEL_LOG, "a") as _f:
        _f.write(_sjson.dumps(row, sort_keys=True) + "\\n")


def _sentinel_reset():
    _sentinel_run["i"] += 1
    _sentinel_run["k"] = 0
    _sentinel_run["key"] = "%s/%d" % (_SENTINEL_PAIR, _sentinel_run["i"])
    _dose_rows = _SENTINEL_SCHEDULES.get(_SENTINEL_DOSE, {})
    _row = _dose_rows.get(_sentinel_run["key"])
    _sentinel_run["frames"] = None if _row is None else frozenset(_row["brake_frames"])
    _sentinel_write({
        "reset": True,
        "run": _sentinel_run["i"],
        "class": _SENTINEL_CLASS,
        "pair": _SENTINEL_SEQUENCE,
        "dose": _SENTINEL_DOSE,
    })

def _sentinel_intervene(out):
    base = [[float(x), float(y)] for x, y in out.trajectory.tolist()]
    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    k = _sentinel_run["k"]
    _sentinel_run["k"] += 1
    if _sentinel_run["frames"] is None:
        _sentinel_write({
            "schedule_missing": True,
            "schedule_key": _sentinel_run["key"],
            "run": _sentinel_run["i"],
            "class": _SENTINEL_CLASS,
            "pair": _SENTINEL_SEQUENCE,
            "dose": _SENTINEL_DOSE,
            "frame_index": k,
        })
        raise RuntimeError("iteration-135 frozen schedule row missing")
    scheduled = k in _sentinel_run["frames"]
    returned = [[0.0, 0.0] for _ in range(len(base))] if scheduled else base
    _sentinel_write({
        "frame": True,
        "scheduled": scheduled,
        "run": _sentinel_run["i"],
        "class": _SENTINEL_CLASS,
        "pair": _SENTINEL_SEQUENCE,
        "dose": _SENTINEL_DOSE,
        "frame_index": k,
        "base_trajectory": base,
        "returned_trajectory": returned,
    })
    if scheduled:
        _sentinel_write({
            "brake": True,
            "run": _sentinel_run["i"],
            "class": _SENTINEL_CLASS,
            "pair": _SENTINEL_SEQUENCE,
            "dose": _SENTINEL_DOSE,
            "frame_index": k,
        })
    return returned


'''

anchor = '@app.get("/alive")'
assert anchor in src
src = src.replace(anchor, HELPERS + anchor, 1)
infer_old = (
    "    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
    "    return InferenceOutputs(\n"
    "        trajectory=uniad_output.trajectory.tolist(),"
)
infer_new = (
    "    uniad_output = uniad_runner.forward_inference(uniad_input)\n"
    "    return InferenceOutputs(\n"
    "        trajectory=_sentinel_intervene(uniad_output),"
)
assert infer_old in src
src = src.replace(infer_old, infer_new, 1)
reset_old = "async def reset_runner() -> bool:\n    uniad_runner.reset()"
reset_new = "async def reset_runner() -> bool:\n    _sentinel_reset()\n    uniad_runner.reset()"
assert reset_old in src
src = src.replace(reset_old, reset_new, 1)
open(SRV, "w").write(src)
print("BLIND_DOSE_PATCHED")
