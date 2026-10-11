# Engineering basis and limits — 11 October 2026

The immediate uncertainty is action availability. A finite, auditable local maneuver screen
can answer a narrower question before another GPU run or a new information model. It separates
source geometry, available observations, candidate action, model outcome and full-scene unknowns.
The controller is deliberately specified as a diagnostic comparator, not an unnoticed replacement
for the historical planner. No private OpenAI, SpaceX, Tesla or Mobileye process is asserted.

Public primary guidance reviewed on 11 October 2026:

- TUM CommonRoad [Drivability Checker](https://commonroad.in.tum.de/tools/drivability-checker),
  unversioned public overview: collision avoidance, model feasibility and road compliance are
  separate checks. Application here: preserve background/road unknowns even if foreground and
  model checks pass. No CommonRoad conformance or benchmark ranking is claimed.
- CommonRoad [dynamic-obstacle collision tutorial](https://cps.pages.gitlab.lrz.de/commonroad-drivability-checker/05_collision_checks_dynamic_obstacles.html),
  documentation version 2025.4.0; page publication date not supplied. Its batch collision workflow
  includes between-sample occupancy preprocessing. Application here: a separately checked
  conservative interpolation enclosure, with an explicit rotation bound and unresolved status.
  We do not install CommonRoad or claim to execute its checker.
- The dated OpenAI, NASA, NIST and automotive source review remains in Iter152
  ENGINEERING_REVIEW.md and proof/standards_catalogue_review.json. These public materials support
  evidence discipline, not institutional endorsement, normative compliance or a global 2026 ranking.

The finite library, stationary-obstacle extension, simple kinematic model, source completion rule,
and exposed scenario limit every conclusion. A model candidate must undergo a separate full-scene
validation, including real source background collision and available controls, before being called
an observed simulator recovery. A nonlinear optimizer is unnecessary for this first finite screen;
its sophistication would not substitute for independent outcome checks or missing road evidence.
