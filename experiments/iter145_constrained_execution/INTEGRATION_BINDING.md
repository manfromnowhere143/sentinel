# Simulator implementation binding

2026-10-10, before new integration measurements. This specifies the Iter145
implementation within the registered new timing regime. The 28-input optimizer
qualification does not qualify a live simulator or the shorter nominal horizon.

Nominal planner output is six cumulative lidar-frame positions (right, forward).
The pinned base configuration sets `planning_steps=6`; its planning head passes
0.5 seconds to collision optimization, and the pinned HUGSIM driver records that
same knot interval. Bind six future times .5 through3 seconds, prepend measured
ego state, interpolate only the supported .25-second grid:13 states/12 controls.
Segment headings use atan2(right displacement, forward displacement); zero-length
segments retain the previous heading. Speeds are segment distance/.5 seconds.
Transform into the measured world pose. Preserve the supplied current signed speed.
These explicit rules replace the historical untimed interpolation/heading rule.

Attack actors use their actual source-created sampler (including custom grids and
bounds), a5-second sampling horizon, deterministic lowest-index minimum cost and
the Iter144 ten-tick replan interval. This deliberately overrides the historical
global ATTACK_FREQ and .1-second pointer execution; it does not reproduce historical
actor policy. Forecasts share the pre-step snapshot. Neighbors exclude self by
identity; ego remains the explicit target. Constant/IDM retain their source update
methods. Unicycle uses its source clock and native heading convention, and rejects
time outside its trained timestamp support. Unknown types, reverse Attack origins,
missing IDM routes and unsupported clocks stop qualification explicitly.

A fresh environment is attached before its sole reset. Reset restores steering and
last-action fields as well as the original source reset fields. Subsequent resets
are rejected; replicas use fresh processes. Actor transforms use consumed position
and heading together, retaining source model-axis/rectification offsets and ground
height convention. Both actual rendering and collision read that transform object.
CPU stubs qualify this wiring, not CUDA rasterization or physical collision fidelity.

Assert dt=.25, wheelbase2.7, acceleration bounds±2 and steering-rate bounds±pi/12.
The source misleadingly names steering-rate bounds min_steer/max_steer; it applies
them to action_space['steer_rate']. Enforce the controller's cumulative angle bound
±pi/3 separately. Record failed admission and stop; never substitute a control.
Each observation and delivery carries episode, frame and simulation time. Strict
typed plan bytes and hashes bind nominal/proposed/delivered arrays. Bounded runner
logs reset, decision, application, render/collision observations and stopping reason.

Actual pilot YAML bodies, asset closure, installed runtime and resource state are
still unobserved because cloud credential refresh requires operator reauthentication.
No CPU fixture may mark those gates satisfied. No live launch is authorized by a
placeholder price, budget, asset manifest or synthetic passing resource fixture.

Formal CPU evidence capture: four fixed cases (ego speeds0 and4, nominal right
displacements0 or .03*i^2 and forward displacements2*i at i=1..6), each repeated
twice in a fresh environment,12 advances per invocation. Four actor types share
the source_fixture.py initial states, with actual source AttackPlanner defaults.
Independent replay must check every time, typed plan, nominal coordinate transform,
control certificate, ego transition, new actor transform, six-camera/collision
state sharing and numerical replicas. The CPU polygon-intersection substitute is
explicit because local Shapely is unavailable; actual GPU/GEOS remains unqualified.
