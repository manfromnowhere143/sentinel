SRV = '/opt/sentinel-stack/UniAD/inference/server.py'
s = open(SRV).read()
if 'SENTINEL_MODE' in s:
    print('MODES_ALREADY'); raise SystemExit
anchor = '''    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    try:
'''
branch = '''    if _sos.environ.get("SENTINEL_ENABLED", "0") != "1":
        return base
    try:
        _smode = _sos.environ.get("SENTINEL_MODE", "ttc")
        if _smode == "always":  # ablation: brake every frame -> should wreck the clean scene
            _sentinel_run["braking"] = True
            try:
                with open(_SENTINEL_LOG, "a") as f:
                    f.write(_sjson.dumps({"brake": True, "run": _sentinel_run["i"], "mode": "always"}) + "\\n")
            except Exception:
                pass
            return [[0.0, 0.0] for _ in range(len(base))]
        if _smode == "proximity":  # ablation: brake on CURRENT distance only (no forecast/closing)
            proxd = float(_sos.environ.get("SENTINEL_PROXD", "6.0"))
            _ms = float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3"))
            _aux = out.aux_outputs.to_json()
            _objs = _aux.get("objects_in_bev") or []
            _sc = _aux.get("object_scores") or []
            _mg = 1e9
            for _i in range(min(len(_objs), len(_sc))):
                if _sc[_i] and _sc[_i] >= _ms:
                    _g = _smath.hypot(float(_objs[_i][0]), float(_objs[_i][1]))
                    if _g < _mg:
                        _mg = _g
            if _sentinel_run.get("braking") or _mg < proxd:
                _sentinel_run["braking"] = True
                try:
                    with open(_SENTINEL_LOG, "a") as f:
                        f.write(_sjson.dumps({"brake": True, "run": _sentinel_run["i"],
                                              "mode": "proximity", "gap": round(_mg, 2)}) + "\\n")
                except Exception:
                    pass
                return [[0.0, 0.0] for _ in range(len(base))]
            return base
'''
assert anchor in s, 'intervene anchor not found'
s = s.replace(anchor, branch, 1)
open(SRV, 'w').write(s)
print('MODES_PATCHED')
