# Common checkpoint objective and budget-derived branching width

For retained root frame f in {12,13,14,15}, let n=16-f. The state is
[x,y,heading,speed,steering], and stored route vertices are [y,x]. Convert the route
to Cartesian points q_i=(route_i[1],route_i[0]). Let l_0=0 and accumulate
l_i=l_(i-1)+hypot(q_i.x-q_(i-1).x,q_i.y-q_(i-1).y) in route order. Adjacent route
vertices must be distinct. Choose the nearest vertex k, breaking ties by earliest
index. Define v_target=min(6,max(0,v_root)) and

`station = min(l_last, l_k + v_target * n / 4)`.

Choose the first route index j with l_j >= station. The seed target position is
q_j, heading is the forward segment tangent (the last segment at the route end),
speed is v_target and steering is zero. The root is never projected or changed;
clamping applies only to the proposed target speed. The target clock is frame 16.
The rule is nominal-speed geometric lookahead, not an optimized feasible endpoint.
The independent checker reconstructs nearest index, station, selected vertex,
heading and target fields without importing the producer target function.

For both arms, success is a contiguous, fully admissible continuation from the
exact root through frame 16. No sampled-target position or speed tolerance is part
of that diagnostic success condition. The generator keeps its original target
matching flags as internal records; the wrapper's witness criterion is distinct.
The beam keeps its existing route guidance. This is a method comparison under a
common feasibility objective, not an isolated representational-capacity test.

A depth-n breadth-first beam with at most A successors per node and width w uses
at most `A * (1 + w * (n-1))` transitions: one expanded root, then at most w parents
at each subsequent depth. With A=18 and n<=4, w=2 gives at most 126 transitions;
w=3 can require 180. Width two is therefore the largest fixed integer satisfying
the 128-transition ceiling for all retained depths without relying on rejection,
deduplication or an early witness. A narrow beam can discard a useful path; the
adverse constructed control explicitly exhibits that loss. This bound supplies
work feasibility, not completeness, optimality, safety or success probability.

Let P_i and B_i indicate admitted checkpoint witnesses from the program and beam
arms at root i. Censored outcomes are undefined. Gains are observed pairs with
(P_i,B_i)=(0,1); losses are (1,0). Report these discordant counts and the two
concordant counts. The claim requires at least one gain, no loss and no unresolved
pair. A known loss is sufficient to contradict retention. Otherwise censoring
prevents a complete-population verdict. These are dependent roots from one exposed
case, so no independent-case significance or general success-rate claim is made.
