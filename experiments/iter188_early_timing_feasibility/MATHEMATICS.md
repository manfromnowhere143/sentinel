# Necessary one-step timing exclusion and numerical envelope

## Quantifiers and model

For each frozen endpoint, consider every binary64 acceleration and steering-rate
pair satisfying the retained physical inequalities. A certificate shows that each
such pair either violates a physical constraint or makes the next route index
complete before frame 32. Consequently no source-admissible continuation through
the final required checkpoint can start there. It does not explain why search
selected that endpoint or exclude a different path from the root.

The source updates speed v'=fl(v+fl(a/4)) and steering first. Its position then
uses the OLD heading: x'=fl(x+fl(fl(v'*cos(h))/4)), with the analogous sine expression
for y. Steering affects the next heading, not this next position. The certificate
therefore bounds acceleration/speed while allowing every steering choice. Dropping
yaw, lateral, steering, collision and route-distance restrictions is a superset
relaxation: it can weaken exclusion, never justify a feasible joint control.

## Directed enclosure and exact predicate

Use the literal source tolerances A=fl(2+1e-12), accepted updated speed between
-1e-12 and fl(6+1e-12). Enclose every multiply and add by moving the minimum rounded
endpoint one representable binary64 value downward and the maximum upward. Basic
IEEE arithmetic is monotone on the bounded finite intervals. Multiplication takes
all four endpoint products. Intersect the resulting speed interval with the accepted
speed limits. Propagate it through the captured actual libm cosine and sine values.
No claim about an ideal trigonometric value is needed for this source-program property.

The producer evaluates floating operations then nextafter. The checker instead
constructs exact rational endpoint operations, rounds those independently to
binary64 and moves outward. It requires the same canonical enclosure. At each
accepted scalar probe, the independent physical position must also lie in the box.

Positions/headings and route coordinates are bounded in absolute value by 1000;
updated speeds by the accepted limits. The resulting next-position box must lie
strictly inside [-1002,1002]^2. Route samples are (y,x); state positions are (x,y).
Partition route indices using the literal binary64 predicate (index+1)/(0.9*N)>=1.
Choose the completing vertex nearest the exact rational box center; lower index
breaks center ties. For every noncompleting vertex qj and completing anchor q0,

    G_j(p) = ||p-qj||^2 - ||p-q0||^2
           = ||qj||^2 - ||q0||^2 + 2*(q0-qj) dot p.

G is affine. The producer minimizes each coordinate term at its appropriate box
endpoint using exact rational arithmetic. The independent checker evaluates the
original squared-distance differences at all four corners. Both retain the exact
minimum gap as a reduced numerator/positive-denominator pair. A strict comparison
against the guard below establishes that a completing vertex is nearer than EVERY
noncompleting vertex throughout the enclosure. Other completing vertices may be
nearer still. Exact/near ties remain uncertified; no tie direction is guessed.

## Derivation of the numerical comparison guard

The actual producer route predicate uses NumPy's two-dimensional Euclidean norm;
the separate scalar predicate uses math.hypot. Their ordering must survive rounding,
not merely hold over exact reals. Assume ordinary binary64 basic operations and
IEEE square root, with no unsafe fast-math replacement; math.hypot has its documented
less-than-one-ulp error on the observed Python 3.14 runtime. Computed libm coefficients
are treated as actual source coefficients and are checked in [-1,1]. This is a
conditional numerical proof, not a formally verified compiler or library.

Exact coordinate differences are less than 2048. Conservatively, subtraction error
is at most 2^-42, squaring roundoff at most 2^-30, and two-term sum roundoff at most
2^-29. With a norm less than 4096, allow square-root/hypot error 2^-40. One computed
norm squared differs from the exact squared distance by less than

    E = 2*(4096*2^-42 + 2^-84 + 2^-30)
        + 2^-29 + 8192*2^-40 + 2^-80 < 2^-25.

The same bound dominates the simpler hypot/subtraction error chain. The strict gap
guard is 2^-23, greater than 2E. Hence computed noncompleting norm squared remains
strictly greater than the completing norm squared. Both norms are nonnegative, so
the computed norms also have that order. Exact rational tests retain this inequality.
There is no arbitrary post-outcome epsilon adjustment. Unknown means this sufficient
certificate did not establish exclusion, including insufficient numerical margin.

## Positive evidence and counterchecks

Every actual transition on all nine retained completed paths is replayed with a
separate scalar motion/control implementation and must not be excluded. Exact
case/frame/state matches bind endpoints to their previously admitted complete
suffixes. That is positive existence evidence within the retained model. Historical
point-cloud/collision admission is reused, not rerun or upgraded by this audit.

The fixed finite scalar grid also checks the coupled yaw and lateral bounds. One
kinematically valid noncompleting next action refutes a forced-completion certificate,
but does not prove a collision-free or full successful continuation. Record such
counterchecks separately. All other endpoints stay unknown; no probability or
population claim is estimated from duplicate, repeatedly exposed development states.
