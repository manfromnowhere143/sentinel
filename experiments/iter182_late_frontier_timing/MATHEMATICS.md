# Necessary timing constraints and their numerical scope

States are (x,y,heading,v,steering). Positions, headings and route coordinates
are finite with absolute value <=1000; accepted root speed is in
[-1e-12,6+1e-12]. The fixed source has dt=1/4, acceleration bound 2, speed bound 6.
Route samples are supplied as (y,x). The literal source expression
(index+1)/(0.9*N) defines completion and checkpoint partitions, including its
binary64 evaluation. Source transition first updates v and steering, then updates
x,y using **the old heading** and updated v, then updates heading. Steering cannot
change the next-position direction in this source implementation.

Progress certificate: retain Iter179's bound and separate corner checker, extending
the domain to at most eight remaining steps. With epsilon=2e-12 and n=32-frame,
S=sum(j=1..n) min(6+epsilon, |v|+j*(2+epsilon)/4)/4 + n*1e-8.
Every reachable position is contained in the square centered at (x,y) of radius S
under the declared numerical model. Choose the nearest checkpoint-disallowed
vertex q0 at the root (exact squared distance; lower index breaks ties). For every
checkpoint-allowed vertex qj, minimize ||p-qj||^2-||p-q0||^2 over the square.
The producer uses the affine expression; the independent checker uses four corners.
If every gap exceeds 1e-6, some disallowed vertex is nearer than every allowed
vertex throughout the box: checkpoint progress is impossible within this model.
Ignoring steering, yaw, collision and route constraints enlarges the reachable set.

Premature-completion certificate: applicable only when frame+1<32 and 32 is the
last required checkpoint. Let epsilon=2e-12 and
L=max(-epsilon, v-(2+epsilon)/4-epsilon),
U=min(6+epsilon, v+(2+epsilon)/4+epsilon).
These enclose every accepted updated speed, allowing the physical tolerance and
floating additions. For each current computed binary64 coefficient c=cos(heading)
or sin(heading), enclose position+v'*c/4 for v' in [L,U], then expand each end by
1e-8. Compute interval endpoints as exact rational numbers from binary64 inputs.
Select the completing route vertex nearest the box center, with exact squared
distance and lower-index tie rule. For every noncompleting vertex, the squared
distance difference from this completing anchor is affine in position. If its
minimum exceeds 1e-6 everywhere in the box, the next accepted physical transition
must complete early and cannot be an admissible continuation. Earlier physical
rejections still have precedence; this certificate does not relabel them.

The checker reconstructs speed limits and all four corners separately, validates
partition, anchor and rational representation, and compares exact gap/status.
The producer-bound implementation is never imported by the independent checker.
At frame31 the certificate is inapplicable, all numeric certificate fields are
null and excluded=false; it is not evidence that a frame32 continuation exists.

Numerical scope: exact rational inequalities over the declared outward boxes.
Computed libm values are treated as the actual source coefficients. The 1e-8
coordinate guard exceeds binary64 multiply/add errors at this bounded scale;
the strict 1e-6 squared-distance margin separates the comparison from nearest-index
rounding. This is a bounded source-model argument, not a formal proof for arbitrary
libm implementations, fast-math compilers, unbounded domains, or physical vehicles.
No coefficient approximation is substituted into the source dynamics. Replay
disagreement, nonfinite/out-of-domain input or a verified counter-witness invalidates
admission; no bound is silently weakened after observing results.

Constructed controls cover horizons five through eight, nine-step rejection,
exact boundary/insufficient-margin cases, safe waiting and negative-heading
counterexamples, completion at the checkpoint, floating speed tolerances, altered
partitions/anchors/intervals/gaps, and scene-separated collision masks. Sampling
controls validates examples; it is not the justification of continuous exclusion.
