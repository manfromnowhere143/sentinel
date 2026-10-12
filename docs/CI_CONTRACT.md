# CI scope after the Iter155 presentation update

12 October 2026. Daniel requested repair of the failing hosted checks alongside the
Sentinel instrument update. This is an operational CI correction, not an experiment,
a new publication-lineage admission, or a change to accepted historical evidence.

The default branch's README now presents research through Iter155. The retained
`MISSION_STATE.json` and Iter135 publication machinery still describe the earlier
control contract. Feeding today's Git HEAD and front page into those historical
audits falsely asks the old contract to admit later documentation commits.

The historical contract is now replayed at its exact revision:
`8c118b74c699bf0f139f9bd659192bad06b895f8`. The helper constructs a separate local Git
view with that real HEAD, its original files and its declared upstream reference.
It invokes the original state validator. No probe is mocked, no historical
validator is relaxed, and no old commit or receipt is rewritten. Large evidence
objects remain in Git; only small files needed by these checks are materialized.
The temporary view is removed after validation. No provider or network probe runs.

The current checkout must preserve the archived mission bytes. A retained known-bad
changes those bytes and proves rejection before replay. Iter123 and Iter131 audits
read the historical view; the latter still fails closed without live-probe evidence.
The complete current source test suite, hostile publication tests, supply-chain
verification, locked dependency checks and current documentation link/diagram and
experiment-coverage checks continue to execute. Historical required wording is
checked on historical documents, not imposed on the current front page.

A pass establishes these stated checks. It does not admit the current HEAD as an
Iter135 launch source, erase earlier red runs, or confer scientific validity on a
new result. Research outcomes keep their own source, replay and scope requirements.
