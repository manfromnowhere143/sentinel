# Iteration 18, offline gate — O2 fails by one frame; the gate holds and the GPU stays off

The tracking layer ([`../../sentinel/tracker.py`](../../sentinel/tracker.py), six unit tests)
was evaluated against the pre-registered offline gate ([HYPOTHESIS.md](HYPOTHESIS.md)) by
replaying the committed iteration-17 evidence — world frame reconstructed from the committed
per-run ego poses; harness [`replay_i17.py`](replay_i17.py), output committed in
[`proof/replay_i17_output.txt`](proof/replay_i17_output.txt).

## O2 — the flicker repair: 12 of 13, and the bar said 13

In side-0108's colliding runs (0, 2, 3, 4), the router logged 13 unsafe crawl frames. With the
tracker's velocity persisting through the identity breaks, the overlap predicate mandates the
stop in **12 of them**. The single miss (run 3) sits at a tracker-overlap distance of **2.2 m
against the frozen 2.0 m margin** — 20 centimeters outside.

**The pre-registered bar was "every frame." 12/13 fails it, and per the gate rule, no
closed-loop run launches on this evidence.**

Reported with it, because the evidence earns it:

- The tracker does what it was designed to do: in the mid-crossing frames where the raw
  projection was blind (logged overlap distances 4.6–6.9 m), the tracker sees the crossing
  actor at 5–7 m/s within 0.5–1.1 m of the corridor. Velocity continuity through identity
  switches is real and recovered.
- Retention elsewhere: 80% of non-0108 crawl frames remain crawls (156/196) — the mechanism
  does not go vacuous under the tracker.
- **A correction, kept on the record:** an initial frame-level diagnosis (tracker fed only
  decision frames, starving its state) suggested run 0's threat was absent from detections
  entirely. The correct full-stream replay refutes that reading — run 0 converts 3/3. The
  binding constraint identified by iterations 14 and 17 stands as *tracking* quality; no
  detection-gap layer is established by this data.

## O3 — method-limited in this harness, held open

The clean-scene comparison as implemented contrasts logged *latched* frames with instantaneous
tracker triggers — not a like-for-like pair. O3 is therefore **not scored** here; a fair
instantaneous-vs-instantaneous version belongs to any future offline registration. O1 (the VAD
jitter kill) was not reached: the gate already fails at O2.

## What may follow (named, not built)

The single missed frame invites a tracker-adapted margin (2.2 m would have converted it). That
is exactly the kind of post-hoc parameter fit the gate exists to prevent: adjusting the margin
to the one scene that failed is overfitting until proven otherwise. If pursued, it requires a
fresh offline pre-registration with the overfitting guard stated (retention across all pairs at
the new margin, measured on this same committed evidence, bars frozen first) — and it should be
weighed against the alternative reading: one borderline frame in an open-loop replay (which
cannot model how converted stops would reshape subsequent frames) may simply be the fidelity
floor of offline gating.

## Verdict

Offline gate: **not passed** (O2 12/13 vs an every-frame bar). Closed-loop arms A1/A2 do not
launch. The tracker layer itself — with its tests — remains in the library: the offline result
shows it repairs the measured velocity-flicker class, and the deployment flip's feasibility
(+0.226, CI excluding zero, iteration 17) still stands as the target the next properly
registered design must reach *with* safety.
