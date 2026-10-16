"""One isolated native qualification process; never runs a scene search."""

import argparse
import time
from pathlib import Path
from .common import document, write, rss, require
from .fixtures import compatibility, extra
from .retained import transport


def run(library, mode, output, parent=False, index=None, paths=None):
    started = time.monotonic()
    if mode in ("empty", "approximate", "exact"):
        result = compatibility(library, mode, parent)
    elif mode == "retained":
        result = transport(library, document(paths.parent, paths.name)[index])
    elif mode.startswith("reject_"):
        try:
            extra(library, mutation=mode.removeprefix("reject_"))
        except ValueError as error:
            result = dict(status="rejected", reason=str(error))
        else:
            result = dict(status="accepted_corruption", reason=None)
    else:
        result = extra(library, expiry=mode.removeprefix("expiry_") if mode != "extra" else None)
    write(output, result)
    resources = dict(elapsed_seconds=time.monotonic() - started, peak_rss_bytes=rss())
    write(output.with_suffix(".resources.json"), resources)
    require(
        resources["elapsed_seconds"] <= 20 and resources["peak_rss_bytes"] <= 1073741824,
        "child_resources",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--mode", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--parent", action="store_true")
    p.add_argument("--index", type=int)
    p.add_argument("--paths", type=Path)
    a = p.parse_args()
    run(a.library, a.mode, a.output, a.parent, a.index, a.paths)
