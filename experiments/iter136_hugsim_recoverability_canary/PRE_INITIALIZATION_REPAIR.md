# Pre-initialization adapter repair, 2026-10-09

The first reference launch failed. Its unmodified raw proof was committed as
`1756de8aa5948bebed08c860e1b4752f7cbf9661` before diagnosis. It remains visible at
[proof/live/reference_a](proof/live/reference_a/episode.json).

The traceback fails inside Gym's `load_env_creator`, while importing the environment
class. The environment constructor was never invoked. There was no reset, rendered
observation, client observation delivery, action, step, collision measurement or completed
trace. The trace contains only its header. This is a failed launch before episode
initialization, not a scientific null or a completed reference.

The agent's new launcher mistakenly put the client-only compatibility shim on the
simulator's `PYTHONPATH`. That replaces Torch SVD with a Python wrapper Kornia cannot
compile. The historical simulator launcher does not include this shim; the historical
client wrapper does. Importing `closed_loop` alone failed to expose the problem because
Gym loads the actual environment class lazily.

The [retained diagnostic](proof/simulator_import_diagnosis.json) repeats the exact
environment-class import, without constructing a simulator. Including the shim fails;
scoping the simulator path correctly succeeds on the same host and environment. This is
the known-bad for the newly added environment-class import check.

Before any driving observation, the execution adapter is corrected to remove the shim
from the simulator path. The client retains its exact original shim and image. No
simulator, actor, client, monitor, seed, intervention, comparison, case or outcome rule
changes. New control and output directories have a `v2` suffix; the failed directory and
original runtime manifest remain intact. The corrected binding is in
[proof/runtime_v2/runtime_manifest.json](proof/runtime_v2/runtime_manifest.json).

This continuation uses the preregistered allowance to diagnose infrastructure failure
before an episode starts. It does not retry an initialized or invalid driving episode.
The failed launch counts as one failed launch and zero initialized simulation episodes;
both counts will be reported. The original five-episode maximum and session deadline
remain in force, including time spent on this repair. Any failure after environment
initialization is an attempted episode and will not be retried in this canary.
