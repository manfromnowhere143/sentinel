# Implement the existing terminal-time requirement

Iter166's raw paths exposed an adapter defect: route completion preceded a mandatory
checkpoint, so independent admission rejected the first case. Merely trusting the
OMPL exact-solution flag would have changed Sentinel's acceptance contract.

One correction: reject a proposed terminal edge when its absolute frame is earlier
than the final mandatory checkpoint. Reject off-grid checkpoint times. Keep released
OMPL2.0.1, the same native bridge and physical callbacks, all four cases and seeds,
state-distance weights, sampler, proposal family, 18,000 attempts, 120 seconds and
96 actions unchanged. Compare no performance metric against a redefined goal.

This is exposed development qualification following a retained invalid result,
not a fresh held-out comparison. Acceptance still requires all4 paths independently
passing full masks, motion, constraints and both checkpoint observations. Any valid
bounded miss contradicts this fixed adapter's all-case qualification claim.
No seed tuning, wider budget, source-scene RRT, GPU, provider or native driving.

Alternatives are to waive unobserved checkpoints or continue after task completion;
both would change the current scientific contract. Neither is adopted. A future
mission may explicitly choose a different terminal/deadline semantics prospectively.
The useful falsifier here is unchanged: one valid capped miss prevents qualification.
