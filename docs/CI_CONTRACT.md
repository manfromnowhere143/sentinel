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

On the current research lineage, Ruff additionally encountered 832 findings in
168 immutable execution and editorial source copies. Those exact paths are now
excluded from maintained-source lint and individually SHA-256 bound by the
supply-chain verifier, which runs before Ruff. Every archived byte remains intact.
The pinned `pyproject.toml` identity is advanced for that explicit inventory; no
workflow step, action reference, dependency lock or hostile control is removed.
Known-bads prove that an altered archived byte is rejected and that a new Python
file beside an archive is still linted. There is no directory-wide exclusion.

Once lint could finish, the research suite exposed missing CPU test dependencies:
Shapely and PyTorch. Both Python-minor locks now retain exact wheel hashes for
Shapely 2.1.2, PyTorch 2.10.0+cpu and their resolved dependencies. The original
numeric-stack pins remain unchanged. The only additional wheel listing is the
exact upstream `--find-links https://download.pytorch.org/whl/cpu/torch/` directive
at the start of each lock. Both parsers reject other URLs, other option forms and
duplicate directives; retained known-bads exercise those failures. Installation
still requires hashes, binary wheels, no dependency resolution, a fresh isolated
venv and verified pip-report/installed-metadata agreement. No workflow command,
action reference or test is removed. The resolution record identifies target
Python minors, URLs and hashes. This CPU CI stack is not the historical native
CUDA experiment environment and does not retroactively rerun those experiments.

The subsequent full research suite found 11 failing tests on both Python minors.
PyYAML 6.0.3 is now hash-locked for the Iter145 source-import tests. Ruff is invoked
through the test interpreter, so the isolated venv does not depend on shell PATH.
Iter133 and the historical handoff action contract read their exact archived
inputs; current false-IDLE handoff checks remain current. The rollback control
now expects the current Iter155 result inventory. Iter142's reference check uses
a real disposable Git graph, exercising a valid ancestor, an absent branch and
an unrelated commit instead of depending on a developer's local branch. No
scientific source or archived execution byte is altered by these fixture repairs.
