# Execution design review

The protocol is frozen at `e7994353d3d496fd10357a98418871f0c0815619`.
This implementation adds delivery capture around the retained released monitor and
uses its current output for references, or the original nominal array for continuation.
The monitor function itself is unchanged. The wrapper requires it enabled, verifies a
new decision record, rejects errors and input mutation, and captures typed arrays
before pickle transport. No simulator or historical source file is edited.

The generated server driver retains Iter136 seeds, double reset and 401-action loop.
Iter137 numerical source, parameters and replay remain unchanged. Iter139 structural
checks are reused through an explicit schema conversion: all Iter141 server inputs
are already selected, so the normalized trace has no server pulse. This reuse is
separate from the new stdlib Decimal implementation of delivery bytes, control
bounds, prefix, paired equality and outcomes.

## Effective controls and declared action space

The pinned `lqr.py` specifies acceleration ±3 m/s², steering-rate ±0.4 rad/s,
steering angle ±pi/3, and prediction dt=0.5. Its solver clips inputs and can adjust
steering rate when clipping the next predicted steering angle. Iter141 records the
receipt first and rejects an out-of-contract result before environment actuation.
The current steering and its next 0.25-second value are checked as well.

The pinned `kinematic.yaml` and environment initialization declare Gym acceleration
±2 and steering-rate ±radians(15), approximately ±0.261799 rad/s. The environment
step does not enforce either declared limit. Both kinds of declared-space violations
and their union are reported separately, with no clipping. The research envelope is
larger; this is an unchanged released-model comparison, not physical feasibility.
The controller predicts at 0.5 seconds, environment at 0.25, and actor candidate
planning at 0.1. The source review in [Iter140](../iter140_contact_actuation/SOURCE_REVIEW.md)
explains the actor feedback and limitations.

## Local and host checks

Local macOS NumPy uses Accelerate, which threadpoolctl does not expose. The local
synthetic fixture mocks only the threadpool observation; the separate bound-host
fixture must run the actual check without a mock. The fixture feeds four changing
nominal plans through the original monitor, typed transport, generated driver,
numerical controller and action recorder, with a first plan contrast at frame 1.
Its route completion and collision labels are synthetic; they establish no recovery.

Retain the initial local failures: the Iter140 virtual environment lacked
threadpoolctl; the ambient environment then exposed no threadpool. The source guard
remains strict. One unused test import was removed after a Ruff finding. Final test
and source receipts establish only their stated scope, not full or hosted CI.

The first live reference must match both the current fresh replica and the retained
Iter139 driving/numerical records. Only declared new client/driver identity and wall
measurements may differ. This makes instrumentation drift an observable failure.
All four raw episode packets must enter the candidate branch before interpretation.
