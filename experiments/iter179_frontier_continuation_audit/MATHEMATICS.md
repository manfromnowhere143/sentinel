# One-sided deadline exclusion and finite continuation witnesses

Let a retained state at frame f have position p and speed v. The next checkpoint
is frame F=16, with n=F-f in {1,2,3,4}; h=1/4 second. The discrete model updates
speed before position. With conservative numerical allowance e=2e-12, define

`S = h sum(j=1..n) min(6+e, abs(v)+j*h*(2+e)) + n*1e-8`.

The mathematical motion equations imply each position coordinate changes by at
most S, using absolute sine/cosine at most one. The added coordinate allowance is
conservative for the selected binary64 implementation on the declared domain.
This is a model-bound diagnostic, not a formal proof about arbitrary libm, hardware
or unmodeled motion. Restrict speed to the existing physical tolerance and position
and route coordinates to absolute value at most 1,000. Do not change any physical,
checkpoint or scalar replay tolerance.

Let A contain every route index whose original route fraction passes every
checkpoint constraint at F. Use the exact existing fraction/comparison expression.
Choose q0 as the closest disallowed route vertex at the root, with the earliest
index breaking an exact squared-distance tie. For each allowed vertex qj, set

`g_j = ||p-qj||^2 - ||p-q0||^2 - 2*S*(|qj_x-q0_x| + |qj_y-q0_y|)`.

The difference of squared distances is affine in position. If every g_j exceeds
1e-6 square metres, q0 remains strictly closer than every allowed vertex throughout
the entire coordinate reach box. Thus no point in that box can select an allowed
nearest-route index: the checkpoint cannot be met in this declared model. The
additional strict separation is conservative; ties and insufficient separation
remain unknown. Exclusion concerns the required progress checkpoint, not collision
inevitability or global unrecoverability.

Producer arithmetic converts the finite input coordinates to exact rational
values and computes the affine lower bound. The independent checker constructs
all four box corners and checks their squared-distance differences directly,
using an iterative speed envelope. It independently reconstructs the route
partition, anchor, rational radius, minimum gap and exclusion. A false-exclusion
witness is an invalid audit, never a reason to weaken the bound after outcomes.

The diagnostic search supplies the complementary kind of evidence: one finite
sequence of physical controls, joined to its retained prefix, whose full scalar
replay reaches frame 16 without violating the existing predicates. A valid state
at frame 16 is not a complete trajectory through the later checkpoint and terminal
route condition. The search changes controls each step, unlike the tested constant
forward programs, but its bounded misses do not exclude unsampled controls.

Do not train a viability classifier or change integrated selection from these
labels in this audit. Retain the model domain, numerical allowances, exposed
population and unresolved cases before any later filter experiment.
