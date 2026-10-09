# Iteration 138 status

Complete. **supported / REPLAY_MATCHED** within one disclosed development case and the
registered numerical controller/runtime contract. Both references have 26 frames, exact
matching driving bytes and numerical controller records; all 52 controller calls independently
replay. Both collide at 6.5 simulated seconds. Zero intervention branches; no episode retries.

Read [RESULT.md](RESULT.md), [STATE.json](STATE.json), [HYPOTHESIS.md](HYPOTHESIS.md) and
[EXECUTION_BINDING.md](EXECUTION_BINDING.md). Numerical repeatability, measured timing and
useful driving outcomes remain separate. In each run, 24/26 full adapter calls exceed 50 ms.
The [next finite intervention design](NEXT_EXPERIMENT_DESIGN.md) is proposed, not preregistered.
Do not extend or retry Iter138; a successor needs a new frozen protocol.

## Host closure

Provider readback confirms **TERMINATED** for original instance `sentinel-gpu`, ID
3834622546652649531, project sunlit-unison-487018-b0, zone us-west1-a. See
[completed stop operation](proof/stop_operation_readback_2.stdout) and
[final provider state](proof/final_provider_state_2.stdout).
[Postflight](proof/postflight_summary.json) matched all 439 bound files, found no owned
experiment processes, running containers or GPU compute applications, and measured 110.625 GiB
free on the execution disk. The owned shutdown timer was cancelled before the explicit stop.

[Resource accounting](proof/resource_accounting.json): one successful start request, one stop
request, 1146.552 seconds between provider start/stop timestamps; 1156.922 seconds from provider
start-operation insertion to stop-operation completion. These are lifecycle observations, not
billed GPU time. No replacement machine, package/image installation or measured retry.

A local `gcloud compute operations wait` status command was unsupported. The error is retained
in [its stderr](proof/stop_operation.stderr); the stop request itself succeeded. Subsequent
readbacks retained the intermediate STOPPING state, then confirmed DONE/TERMINATED. No stop
request was repeated and no scientific evidence was affected.

Local branch: `research/iter138-live-replay`, unpushed. Canonical master remains F17.
Unrelated WIP and the older accepted publication/lifecycle snapshot remain preserved. The
historical Iter135 lifecycle UNKNOWN is not retroactively resolved by this task's host checks.
