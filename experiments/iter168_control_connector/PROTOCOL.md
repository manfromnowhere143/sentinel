# Stopping, waiting and turning qualification

Freeze PLAN, CASES, all source bindings and tests in Git before the initialized
scientific execution. Run the twelve cases in recorded order; each runs depth1
then depth2. Deterministic enumeration has no RNG seed or stochastic repetitions.
The producer receives geometry, target, temporal task and query callback, never
witness actions. Independently replay every constructive witness and every selected
path, including full scalar point masks. Replay motion, control bounds, foreground
sweeps, route constraints and task phases for every attempted edge. Unselected
background classifications are producer evidence only. Preserve that distinction.

Four stops begin at speeds 0.125, 0.375, 1.25 and 2 m/s and require two subsequent
stationary intervals after stopping. Two waits hold position, heading, speed and
steering for four/eight frames, including nonzero steering at rest. Two restarts
wait two/four frames, then reach an explicit moving target. Four turns cover left
and right, two and eight frames. Scalar-constructed witnesses define target states;
these are intentionally disclosed examples, not a representative driving population.

Each task completes only at its exact terminal frame with coordinate tolerances
[x,y,heading,speed,steering] = [0.02,0.02,0.002,0.01,0.002]. Angles use wrapped
heading difference. A wait is observed at every required frame, not inferred from
an early target match. Braking tasks hold zero speed from the specified stop frame.
The long reference route deliberately does not terminate inside these tasks. Route
progress is a constraint, not this study's completion condition. This prospective
local task definition neither waives nor reinterprets Iter166/167's route contract.

Reuse the dt0.25 semi-implicit bicycle model, wheelbase2.7, acceleration2, speed6,
steering/rate bounds, yaw0.95, lateral acceleration4.89, eight-subdivision foreground
sweep with0.25 margin, route distance10, and progress slack0.05. Both fixture
checkpoints are absolute and checked when crossed. The constructed 968-point cloud
and foreground object exercise the existing static predicates; they are synthetic.
Every selected mask must agree with separate scalar classification. A selected
possible-inside count above100 is rejected, including numerical ambiguity.

The successor preserves the complete old proposal set and adds acceleration
-min(2,v/0.25) paired with the same five steering rates; exact duplicates are removed.
Fourteen prespecified speeds qualify proposal coverage and scalar motion separately.
Invalid/nonfinite state inputs fail closed. No velocity clamp hides invalid braking.

Both connectors use the previous six-coordinate weighted distance [1,1,2,.5,2,.01]
and ascending attempt-ID ties. Each call exhaustively evaluates depth1 or depth2,
clipped to remaining time. It selects the closest valid leaf and commits only its
first control. All intermediate checks apply. Stop on the terminal frame, no valid
rollout, time cap or transition cap. Discard a partially evaluated call after a cap;
retain the previously selected partial path. No failed task is missing or retried.

The primary claim requires depth2 to complete all twelve tasks. Report depth1 and
depth2 counts, all per-case misses, attempted transitions and elapsed times. A valid
failure is contradicted, not invalid. Invalid evidence or witnesses invalidate
admission. Neither result permits source-scene use or a real-vehicle safety claim.

Run envelopes from the owned repository root, substituting full committed hashes:

```bash
python3 -m experiments.iter168_control_connector.run --root "$PWD" --source-commit SOURCE
python3 -m experiments.iter168_control_connector.check --root "$PWD" --raw-commit RAW
```

Use an owned external process-group supervisor with310-second caps. Retain start,
finish, exit and reaping receipts. Source freeze precedes producer; raw commit
precedes checker; admission and human-readable closure follow successful checking.
