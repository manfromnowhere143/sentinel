# Pre-initialization runner correction, 2026-10-09

Status: pre-evidence operational amendment; record before another launch command.
The first runner process failed in 0.117309 seconds at its initial Python import:
`ModuleNotFoundError: No module named 'experiments'`. The launcher invoked system
Python on the wrapper without adding its bound packet to PYTHONPATH. The host
integration fixture used an explicit packet path and therefore missed this entry boundary.

The retained host diagnosis shows an empty Iter142 output root, no initialized marker,
no driver invocation and the import error in the supervisor log. No Iter142 simulator
or planner was initialized; no new reference or nominal observation exists. The outer
collector also failed because its required episode.json did not exist. Those errors,
the original start marker and failed coordinator events are retained unchanged.

The incorporated Iter141 pre-initialization diagnosis provision permits correction
within the same budget before an initialized episode, with pre-evidence source changes
recorded. This amendment authorizes exactly one corrected orchestration attempt for
the unchanged three-arm schedule. It does not resume a measured failed episode or
relax scientific admission. The client, driver, controller, monitor, trace, runtime
manifest, INPUTS, endpoints and seeds remain byte-identical. No budget reset.

Supply `PYTHONPATH=<control>/packet` explicitly to the system-Python runner command.
Before that command can initialize anything, run the exact system-Python entrypoint
with `--help`, retain its successful import/argument-parser output, recheck the empty
output root and absence of owned compute. The original failed import is the known-bad
for the missing-path boundary; do not repeat it as an episode.

Use new `bootstrap2` supervisor/launch filenames and a new one-shot
`schedule_bootstrap2` marker. Preserve original `schedule` files and never restart
either marker. The corrected coordinator reads those new completion receipts and
otherwise retains the tested collect/commit/ledger/verify/next-arm order. If this
corrected attempt fails, stop later arms and close the experiment; no further
orchestration attempt is authorized by this amendment. All remaining initialization,
source identity, replay, missingness, resource and shutdown rules remain in force.
