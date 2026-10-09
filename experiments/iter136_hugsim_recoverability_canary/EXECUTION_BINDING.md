# Iteration 136 live execution binding

Recorded before any new simulation episode on 2026-10-09. The third existing-host start
succeeded. Daniel explicitly confirmed Google Cloud access for this task. The original L4
instance, zone and disks are used; no infrastructure substitution is needed.

## Runtime and isolation

The host inventory matched the registered simulator and client revisions, checkpoint,
scenario, shim, released-union client and collision-provenance evaluator. All 394 tracked
files in the two host source repositories were inventoried. The scene, actor model, ground
data, configuration and new instrumentation are bound in the
[runtime manifest](proof/runtime/runtime_manifest.json), SHA-256
`676889cea35c24ce1d26fde6b2613b4710da557e0cbc8c72e290d09d5abf6bbb`.
The manifest contains 409 file hashes. Hash checks repeat before each episode.

The historical client wrapper installs `open3d` and `mediapy` on every invocation. Its
base image lacks both. The same installation was performed once, without an episode, in
an isolated container derived from the retained image
`sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb`.
The resulting image is frozen as
`sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14`.
The [installation log](proof/client_dependency_setup.log) retains package versions and
dependency warnings; successful installation is not a claim of dependency consistency.
The actual client imports and `--help` completed, with the frozen union parameter marker.
Each episode starts a new container from that exact image, with no package installation.
The monitor source, checkpoint, parameters, client seed and inference flags are unchanged.
This records a newly prepared runtime, not exact recreation of a historical environment.

Simulator imports passed under the existing Python 3.11.10 environment: Torch 2.4.1+cu124,
NumPy 1.26.4, gsplat 1.2.0, CUDA available. The client uses Python 3.8.10 and Torch
1.9.1+cu111. The host reports NVIDIA L4 and driver 580.159.03. The simulator environment
has no `pip` module; its attempted `pip freeze` failure is retained. No environment rebuild
was performed. Startup source, lockfile and observed package identities are retained.

The new launcher and base configuration live under
`/datasets/nuscenes-full/hugsim/iter136_control_20261009`. New output lives under
`/datasets/nuscenes-full/hugsim/outputs/iter136-20261009`, which is inside the existing
client output mount. Historical files and outputs are preserved. The simulator runs via
its existing environment interpreter without asking Pixi to resolve or update packages.

## Execution checks and budget

[run_episode.py](run_episode.py) executes one named registered episode. It requires the
bound manifest and source hashes, exact image, idle GPU, no running containers, exclusive
process lock, new output directory and successful required predecessors. Intervention
branches additionally require a matching collision reference pair. Raw episode proof is
committed before outcome interpretation or deciding to launch an intervention branch.

Each episode has the registered 1,200-second timeout. The fixed host-clock deadline is
12:22:31 UTC, conservatively earlier than 120 minutes after the observed provider start;
local and host clocks differed by about 72 seconds during inspection. A new episode needs
1,230 seconds remaining. The launcher requires 100 GiB free and allows 8 GiB projected
output per episode with a 25 GiB reserve; historical eight-slot output totals 988 MiB.
It removes only its own specifically labelled client container on timeout or exit.
The five-episode maximum, no-retry rule, seeds, comparison tolerance, case, intervention
grid, outcome definitions and scientific stopping rules remain as preregistered.

The focused suite now passes 48 tests, including retained known-bads for changed runtime
files/image, symlink substitution, competing work, storage/time limits, repeated output,
failed predecessors and interventions without a matching collision pair. Ruff passes.
These checks establish tooling behavior only. No live driving outcome is asserted here.
