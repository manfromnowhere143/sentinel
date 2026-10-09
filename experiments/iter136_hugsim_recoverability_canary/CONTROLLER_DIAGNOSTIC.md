# Exploratory controller diagnostic registration

Recorded after the reference-pair failure and before the controller fixture runs.
Iteration 136's live verdict is `REPLAY_DIVERGED`; its intervention stage is closed.
No new simulation episode, seed change, tolerance change or intervention is authorized
by this diagnostic. The original instance-runtime deadline remains in force.

Both references have exactly equal first recorded observation hashes, pre-action states
and incoming/executed plan values. Their first steering-rate outputs differ by about
`7.8045e-6`. The pinned controller source sets `max_solve_time=0.05` and checks
`time.perf_counter()` during iterative optimization. This suggests a wall-time-dependent
control mapping. It does not establish the actual iteration counts in the live runs.

Use the retained first reference's first input and pre-action state. Execute only the
exact source `traj2control` function and the existing CPU iLQR solver. Do not construct
the simulator or run a client, renderer or model. Verify the source hashes against the
already committed runtime manifest before execution.

The plan's array dtype was not retained in the JSON trace. Disclose this limitation and
run both `float32` and `float64` reconstructions. For each dtype, run three fresh-solver
calls with the real clock, then two calls for each controlled deadline position of
1, 5, 10, 20 and 100 iterations: 26 CPU solves total. The controlled clock changes only
the module's clock object in the isolated probe process; upstream files, solver weights,
iteration ceiling and convergence threshold remain unchanged. Early convergence is
retained literally. Do not increase repetitions or select another input after results.

Retain elapsed times, clock-read counts, solution lengths, all first-control iterates,
final tracking costs and final commands. Commit raw output before interpretation.
Report whether the same numeric input can yield different commands under different
controlled deadlines, whether identical controlled conditions repeat, and the distance
from each retained live first command to the computed iterate sequences. These are
source-fixture observations, not proof of the live cause, a production controller design,
real-time feasibility, or collision prevention.
