# Iteration 52 - HUGSIM ON-collision timing audit: TIMING_AUDIT_COMPLETE

Status: `TIMING_AUDIT_COMPLETE` (offline post-result audit over committed iteration-48/49
HUGSIM proof only; zero GPU, zero gcloud, zero box reads, zero simulator launches, zero
retuning).

## Process Disclosure

This audit is not blind. Before the hypothesis was frozen, a small prototype timing probe was
run over the already-published HUGSIM evidence to confirm that the ON-arm `eval.json` and
decision logs could support the bins. The prototype counts were disclosed in
`HYPOTHESIS.md`. This result therefore makes no inferential surprise claim and uses no
statistical pass/fail bar.

## Registered Question

Iteration 51 showed that the HUGSIM transfer failure is mostly collision persistence. Iteration
52 asks a narrower question over ON-collision episodes:

When ON still collides, did the released union brake after the ON collision had already appeared,
fail to enter the frozen TTC/CPA monitor surface proxy at all, or brake before the ON collision
and still fail?

## Evidence And Integrity

Inputs were exactly the committed artifacts named in `HYPOTHESIS.md`:

- iteration 48 `proof-stage2/episodes/`;
- iteration 49 `proof-hard/episodes/`;
- iteration 51 `proof-taxonomy/failure_taxonomy_report.json` for cross-checks only.

Analyzer command receipt:
[`proof-timing/analyze_on_collision_timing.command.txt`](proof-timing/analyze_on_collision_timing.command.txt).

Proof outputs:

- [`proof-timing/on_collision_timing_report.json`](proof-timing/on_collision_timing_report.json);
- [`proof-timing/on_collision_timing_pairs.md`](proof-timing/on_collision_timing_pairs.md).

Infrastructure checks passed:

- `104` paired HUGSIM transfer episodes read;
- ON-collision count matched iteration 51 exactly: `92` vs `92`;
- no schema or missing-file infrastructure problem fired.

## Timing Result

Combined timing bins over the `92` ON-collision episodes:

| bin | count |
|---|---:|
| `post_collision_first_brake` | 35 |
| `long_lead_brake` | 26 |
| `no_brake_no_surface_proxy` | 22 |
| `short_lead_brake` | 9 |
| `no_brake_surface_proxy_present` | 0 |
| `unknown_collision_time` | 0 |

Family split:

- `absent_or_post_collision_brake_family`: `57/92`;
- `pre_collision_brake_family`: `35/92`.

The no-brake result is specific: all `22` no-brake ON-collision episodes also had
`0` TTC/CPA surface-proxy rows. No episode fell into `no_brake_surface_proxy_present`.
Under the available scalar decision logs, the monitor did not merely suppress braking after
entering the frozen TTC/CPA proxy; those episodes never entered that proxy.

But timing/surface does not explain everything. In `35/92` ON-collision episodes the monitor
braked before the ON collision appeared, including `26` with more than one second of lead
time. Those cases are the strongest evidence that some HUGSIM failures are not just "brake
earlier"; they require a later audit of hazard surface, planner/path geometry, or HD-Score
composition.

## Dataset Split

Iteration 48 easy+medium ON collisions (`40`):

- no-brake/no-surface-proxy: `10`;
- post-collision first brake: `14`;
- short-lead brake: `1`;
- long-lead brake: `15`;
- absent/post family: `24`;
- pre-collision family: `16`.

Iteration 49 hard/extreme ON collisions (`52`):

- no-brake/no-surface-proxy: `12`;
- post-collision first brake: `21`;
- short-lead brake: `8`;
- long-lead brake: `11`;
- absent/post family: `33`;
- pre-collision family: `19`.

Iteration 49 AttackPlanner split:

- AttackPlanner ON collisions (`30`): absent/post family `18`, pre-collision family `12`;
  bins: no-brake/no-surface `6`, post-collision first brake `12`, short-lead `8`,
  long-lead `4`;
- non-AttackPlanner hard/extreme ON collisions (`22`): absent/post family `15`,
  pre-collision family `7`; bins: no-brake/no-surface `6`, post-collision first brake `9`,
  short-lead `0`, long-lead `7`.

## Interpretation

This decomposes the persistence found in iteration 51:

1. A large family is absent or post-collision braking (`57/92`): either the frozen TTC/CPA
   surface proxy never triggers before collision (`22`) or the first brake arrives after the
   ON collision has already appeared (`35`).
2. A substantial family is pre-collision braking without conversion (`35/92`), including
   `26` long-lead cases. Those cases make a pure "brake earlier" repair story insufficient.
3. The hard/extreme tier remains the sharper boundary: every iteration-49 episode collided
   on the ON arm, and `33/52` were absent/post while `19/52` had pre-collision braking.

The next mature pre-registration should therefore be a hazard-surface / planner-path geometry
audit over the pre-collision-brake persistent cases: did the monitor brake for a geometry that
does not control the eventual HUGSIM collision, or is HD-Score dominated by components outside
collision conversion?

## Boundaries

This result does not change iterations 48, 49, 50, or 51. It makes no new safety, transfer,
deployment, robustness, benchmark-ranking, real-world, monitor-performance, HUGSIM-equivalence,
or retuning claim. The TTC/CPA surface is a scalar proxy, not the full firing predicate, and
the audit cannot identify the true colliding actor.
