from pathlib import Path
import hashlib,json,subprocess
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter145_constrained_execution';P=D/'proof';P.mkdir(parents=True,exist_ok=False);(P/'commands').mkdir()
E=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010');E.mkdir(exist_ok=False)
status=subprocess.check_output(['git','status','--porcelain','-z'],cwd=R).decode().split('\0')
(E/'initial_wip_hashes.json').write_text(json.dumps({s[3:]:hashlib.sha256((R/s[3:]).read_bytes()).hexdigest() if (R/s[3:]).is_file() else None for s in status if s and not s.startswith('??')},indent=2)+'\n')
(E/'initial_index.diff').write_bytes(subprocess.check_output(['git','diff','--cached','--binary'],cwd=R))
(D/'HYPOTHESIS.md').write_text('''# Iter145 constrained controller and simulator qualification

Preregistered 2026-10-10 before new measurements. Parent closed Iter144:
958e9da1ee48029279a9c92d215d7c6d09aeabb6. Daniel directly requested convergence repair,
full simulator integration and asset/resource verification before live execution.
Preserve every earlier result, source generation and dirty workspace change.

## Local optimizer qualification

Use all four Iter144 reference cases, each repeated twice, plus the 20 retained
moving-ego integration inputs. Reuse the exact inputs rather than regenerate them.
Instrument the Iter144 iLQR to retain objective, applied controls and input-change
history without changing its algorithm. Diagnose failure from observations, not from
the iteration-limit label alone. Retain the old solver as comparator.

The prospective candidate is constrained direct shooting with SLSQP, analytic
rollout derivatives and explicit linear actuator constraints. Same .25 s dynamics,
wheelbase2.7, tracking weights [1,1,10,0,0], input weights [1,10], 19 controls,
acceleration±2, steering rate±pi/12, steering angle±pi/3 and signed ego speed.
Decision variables are physically applied controls, so differentiate smooth feasible
motion; enforce rate boxes and cumulative steering bounds separately. This avoids
using the derivative of a clipped requested input as the feasible inward derivative.
This is a new solver policy, not retrospective repair of prior results.

Keep the 100 major-iteration cap. Candidate SLSQP objective tolerance1e-12; a library
success flag alone never qualifies an action. Independently calculate feasibility
(max violation <=1e-9), KKT stationarity (infinity norm <=1e-6), nonnegative multipliers
and complementarity <=1e-7. Store every final state/control, objective, gradient,
constraint slack/multiplier and callback history. Report KKT as first-order local
stationarity, never global optimality for curved trajectories. The convergence metric
changes explicitly from iLQR input-change to KKT, without relabeling old outcomes.
No nonfinite, failed, iteration-limited or uncertified solution may silently actuate.

Use the same retained warm-start generator, then project it to the feasible control
set before optimization. No weight/cap/fixture/seed search. Validate rollout/Jacobians
by central differences away from heading-wrap singularities, and independently replay
final motion, objective and KKT using separate code. Verify straight-reference cost
against a separately solved longitudinal convex quadratic subproblem; a straight
restricted optimum is not a global nonlinear trajectory proof. Keep solver and total
call time separate, and compare numerical replicas within1e-9. If this design fails,
retain the failure and amend prospectively before a replacement design or measurement.

## Simulator integration contract

Carry explicit timestamps from source nominal reference knots through control,
actor execution, observation, collision and rendering. Bind knot times from planner
source/configuration, never invent support beyond the available plan. If its 6 knots
cover .5..3 s, prepend measured state at0 and use the covered .25 s grid through3,
explicitly qualifying that shorter horizon separately from the 19-control fixture.
Use deterministic actor selection and the Iter144 named timing regime. Support the
actual controller types present in all14 pilot YAMLs; unknown types stop admission.
Reset every mutable state exactly once per episode, including steering, timestamps,
actor trajectories/pointers and observation state. Rendering and collision consume
identical new actor positions/headings. Assert runtime dt/wheelbase/limits.

Test actual retained methods with bounded CPU stubs before deployed qualification.
Commit tested integration source before host deployment. Qualify actual GPU rendering,
collision and planner/monitor boundaries with a separately bound finite smoke. Smoke
outcomes are engineering observations and cannot enter the 112-slot recovery study.
Record every initialized smoke and failure; no silent retries or replacements.

## Assets and resource qualification

Read-only provider/source/asset inventory is authorized after this registration.
Only existing sentinel-gpu ID3834622546652649531, project sunlit-unison-487018-b0,
us-west1-a, g2-standard-8/L4. Preserve existing artifacts; no sibling changes, package
upgrades, new instances, bucket changes or scientific study launch from this document.
Before any start bind a dated hourly price upper bound and a finite inspection/smoke
budget, deployable source identity, exact capacity-attempt cap, hard shutdown timer
and cleanup owner in a prospective execution binding. Missing assets stay unavailable.

Verify all14 YAML identities against the unchanged inventory, their scene/model/
checkpoint dependencies, runtime versions and image identity, free local>=15GiB,
remote>=100GiB and projected remaining>=25GiB. No substitution or scene0411 search.
Owned output directories are exclusive. An occupied host or foreign workload stops
inspection/launch rather than terminating unrelated processes. Verify shutdown.
Measure initialization, per-step time, output storage and full-call/controller latency
separately. Establish a conservative feasible study envelope before live preregistration;
resource stops leave missing rows. Do not infer population recovery, safety or state of
the art from successful engineering qualification.

## Evidence order

Commit preregistration, tested source, raw data, then independent interpretation.
Retain known-bads for every new admission layer and exact command stdout/stderr/status.
Publication remains local candidate evidence unless separately validated and published.
Scientific 14-scenario/112-slot live comparison remains unadmitted by this protocol.
''')
base=R/'experiments/iter144_timed_trajectory';m=json.loads((base/'INPUTS.json').read_text());paths=set(m['files'])
paths.update(str(p.relative_to(R)) for p in base.glob('*.py'))
paths.update(['experiments/iter144_timed_trajectory/INPUTS.json','experiments/iter144_timed_trajectory/SOURCE_ADDITION.json','experiments/iter144_timed_trajectory/source/geometry_utils.py.txt','experiments/iter144_timed_trajectory/proof/raw_qualification.json','experiments/iter144_timed_trajectory/proof/study_schedule.json'])
(D/'INPUTS.json').write_text(json.dumps({'schema':'sentinel.iter145.inputs.v1','files':{p:{'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest(),'bytes':(R/p).stat().st_size} for p in sorted(paths)}},indent=2)+'\n')
(D/'STATE.json').write_text(json.dumps(dict(iteration=145,status='preregistered',phase='implementation',cloud_access=False,live_study_episodes=0),indent=2)+'\n')
s=Path('/tmp/sentinel_i144_commit.py').read_text().replace('iter144-timed-trajectory','iter145-constrained-execution').replace('18ca7e2000c22c7cd1d00f31ab81854a25fa2698','958e9da1ee48029279a9c92d215d7c6d09aeabb6').replace('iter144_timed_trajectory','iter145_constrained_execution').replace('i144','i145')
Path('/tmp/sentinel_i145_commit.py').write_text(s)
Path('/tmp/i145_run.py').write_text(Path('/tmp/i144_run.py').read_text().replace('iter144_timed_trajectory','iter145_constrained_execution'))
print(E)
