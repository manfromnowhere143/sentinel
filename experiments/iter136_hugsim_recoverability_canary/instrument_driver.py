"""Generate a separate canary driver from exact pinned upstream bytes, without editing them."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


DRIVER_SHA256 = "42a0c878aa9e365b9e1b1d5e6d902c8fe6e2ee79deac376c23a2bd1ea439c8f5"


def instrument(raw: bytes) -> bytes:
    if hashlib.sha256(raw).hexdigest() != DRIVER_SHA256:
        raise ValueError("upstream driver hash mismatch")
    source = raw.decode()
    replacements = [
        ("import numpy as np\n", "import numpy as np\nfrom replay_trace import Recorder\n"),
        ("    env = gymnasium.make", "    trace = Recorder(output, __file__)\n"
         "    env = gymnasium.make"),
        ('        with open(obs_pipe, "wb") as pipe:',
         '        trace.begin(obs, info, cnt)\n        with open(obs_pipe, "wb") as pipe:'),
        ("        if plan_traj is not None:",
         "        plan_traj = trace.choose(plan_traj)\n        if plan_traj is not None:"),
        ("            done = terminated or truncated or cnt > 400",
         "            done = terminated or truncated or cnt > 400\n"
         "            trace.end_step(action, info, terminated, truncated or cnt > 400)"),
        ('    with open(os.path.join(output, \'data.pkl\'), \'wb\') as wf:',
         "    trace.finish()\n    with open(os.path.join(output, 'data.pkl'), 'wb') as wf:"),
        ('    args = parser.parse_args()',
         '    parser.add_argument("--i136-output-base", required=True)\n'
         '    args = parser.parse_args()\n'
         '    import random\n    import torch\n'
         '    random.seed(136)\n    np.random.seed(136)\n    torch.manual_seed(136)\n'
         '    torch.cuda.manual_seed_all(136)'),
        ("    cfg.base.output_dir = cfg.base.output_dir + args.ad",
         "    cfg.base.output_dir = os.path.abspath(args.i136_output_base)"),
        ("    os.makedirs(output, exist_ok=True)\n",
         "    os.makedirs(output, exist_ok=False)\n"),
        ("        process.kill()\n", "        process.kill()\n        raise\n"),
    ]
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError(f"nonunique source anchor: {before!r}")
        source = source.replace(before, after, 1)
    compile(source, "iter136_closed_loop.py", "exec")
    return source.encode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.source.is_symlink():
        raise ValueError("source symlink")
    data = instrument(args.source.read_bytes())
    with args.destination.open("xb") as stream:
        stream.write(data)
    print(hashlib.sha256(data).hexdigest())
