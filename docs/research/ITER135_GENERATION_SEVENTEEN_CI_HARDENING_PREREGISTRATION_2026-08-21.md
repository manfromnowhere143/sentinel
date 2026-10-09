# Iteration 135 Generation-17 CI hardening preacceptance design record

Status: `preacceptance design record`; proposed, not independently prior, not accepted, not
executed in hosted CI, and not repository-publication, lifecycle, host, GPU, experiment,
scientific, or Odeya authority.

Date: 2026-08-21

## Pre-evidence packet correction (2026-08-22; controlling amendment)

This amendment was made before packet acceptance, source binding, replay, candidate checkout,
hosted CI, or any scientific execution. It controls wherever the original 2026-08-21 text below
conflicts with it. The original bytes and their authority-false output remain retained as negative
evidence; they are not repaired in place and may not be selected back into the ceremony.

The packet at
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260821/ceremony-packet` is rejected.
Its manifest SHA-256 is
`f8372ccc7da17a96835e599f6bea06a54b930a7ff68bb6a9ebfc372badc6d800`. Its sole retained
preflight is `9,245` bytes with SHA-256
`6a49da29482fb4c01a144ec1fb99947281da4b795dbafee693cb8c9dc7e5fa48`. No packet acceptance,
bind, replay, v2 receipt, process record, reducer output, or final operator acceptance exists in
that namespace.

Two pre-acceptance defects invalidate the old packet. First, `CONTRACT.md` named one preflight
`environment` root while the executable schema materialized four distinct roots:
`assigned_environment`, `platform_environment`, `effective_environment`, and
`environment_probe`. Second, the old supervisor admitted finite JSON floats and unbounded Python
integers while the independent reducer rejected all floats and bounded integers; ordinary Python
equality also permitted Boolean/integer aliases at nested fields. The old `25/25` hostile result
did not test these cross-parser states, decoded key/string limits, conventional signed-64
boundaries, or lone-surrogate behavior. A green preflight produced by those bytes therefore does
not establish the packet contract it claimed.

Candidate `ee23c106ad1a3566026013f712a03435315f68f6` is rejected with the packet because its
same-commit prerecord content-addresses that packet and states that the defective hostile suite
closed strict parsing. Rebinding the same object to replacement evidence would select around its
retained prerecord. It remains preserved at
`refs/sentinel-candidates/f17-rejected-packet-ee23c106` and is prohibited from checkout,
execution, binding, publication, or reuse as F17.

The intermediate
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822` namespace is retained as an
unfrozen development staging area. Its packet members and manifest were revised during the
hostile audit, but mutable staging bytes are not acceptance evidence and it may never receive a
preflight, acceptance, bind, replay, receipt, reducer output, or source-admission claim. The only
first replacement evidence namespace was the fresh one-shot materialization at
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r2`. It contains a clean detached
D16 worktree at `355010c4b668c85fcd2647586c56d7a21b8b88d0`, tree
`9b4adcf6d368a3cc650899898b4d3316aa6a9ce8`; the `297,539`-byte external verifier with SHA-256
`4c73ba1c83348a51ea860a88c9b18ed057f391a829882960030b7d68d144451d`; and the owner-only
`38,100`-byte R16 receipt with SHA-256
`31e851778869b46c75c1da78545aee469f48f3b6f54bd78d36d8d1c18422a391`.

The rejected `r2` packet manifest is `2,639` bytes, SHA-256
`249e9e8a6490f72eeb9c885596a6d3a5fecee635f729e7098b4c38c53952ffbc`, with payload SHA-256
`2c44a5c654709d427e91f0c09f39cbcb4a6aac30b6f7b384bc7a60fb74e55787`. It binds these five
additional physical owner files, all at mode `0600` and link count one:

- `contract.json`: `13,790` bytes, SHA-256
  `61e785240234facb48e8102967b4622e7c9b20633027538017e69e9984f1c942`;
- `CONTRACT.md`: `15,718` bytes, SHA-256
  `7212e7b402af5c9f3f7509b25517b7a504d2aeaaeb995bfdb184f1259033b6ab`;
- `supervise_source_admission.py`: `119,956` bytes, SHA-256
  `87d94f8edb414d84557c45b67f77aacb862a2afe14409b357ae5852780b4382d`;
- independently implemented `reduce_source_admission.py`: `85,829` bytes, SHA-256
  `bf09a0788454faeb220855276eccd86aff4ca7762d39de5e94dbbec345f4e945`; and
- `test_source_admission_packet.py`: `99,031` bytes, SHA-256
  `4e52e1b94fb37fd3ecd42818846c736f6dfc38285804807313a0ab67abe96d84`.

The exact R16-bound Python 3.14 `-I -B -S` hostile suite passed `37/37`; the three Python members
also pass pinned Ruff `0.15.20` lint and format checks under Sentinel's exact `pyproject.toml` plus
AST parsing. Both executable parsers accept the exact contract object, path topology, manifest,
payload seal, limitations, inventory, and member identities in their frozen modes. These are
same-packet checks, not independent operator acceptance. No preflight, packet acceptance, bind,
replay, v2 receipt, process record, reducer output, or final operator acceptance exists in `r2`
at this freeze.

An independent pre-preflight hostile audit then found two additional byte defects. First,
`_capture_stage` reads the post-child receipt before it constructs the process record. A harmless
child that created a wrong-mode receipt and exited zero left both no-clobber streams but raised
before `bind.process.json`; receipt mode, link, symlink, oversize, or read faults therefore fail
closed and prohibit replay but are not represented by the promised retained red process record.
Second, reducer `write_no_clobber_json` fsynced the reducer file but never fsynced its parent
directory, contrary to `CONTRACT.md`'s generated-artifact durability claim. The 37-test suite did
not cover either state. These defects reject `r2`; it is retained untouched, and no candidate,
preflight, acceptance, bind, replay, receipt, process record, reducer output, or final acceptance
may ever be attached to it.

The rejected packet also intentionally leaves final source-admission acceptance
`UNDER_SPECIFIED_PROHIBITED`: it authorizes no creation of that artifact. A separately reviewed
pre-creation specification must first freeze its complete schema and bindings, independent-human
authentication and chronology, no-clobber authoring/readback workflow, bounded checkout and local
validation resources, a separate read-only validator, and retained known-bads. The earlier human
packet-acceptance surface can authorize one exact bind and replay only; it cannot accept source
admission, checkout, local candidate execution, publication, hosted CI, provider or host access,
lifecycle observation, GPU use, experiments, scientific claims, or Odeya integration.

The next immutable replacement was the fresh one-shot materialization at
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3`. Its packet manifest is
`2,640` bytes, SHA-256
`82c25835a75f02c97f27ac13a81f0db4775278d7a66a3c19a699046f4dffd81c`, payload SHA-256
`233f17490242e9d19ecd13318ce4c8201598dc17c63d0548e7e0f751b9bdc5cb`. It binds:

- `contract.json`: `13,790` bytes, SHA-256
  `bb994dba02ba7079cd47bcfba212844da31db8b59a93a84bbe91e077977c694f`;
- `CONTRACT.md`: `16,219` bytes, SHA-256
  `71119ce06f5bf80c839bb5de726f6ba66dbfe4cbde02666c6eb29819e3098792`;
- `supervise_source_admission.py`: `121,753` bytes, SHA-256
  `68dbb3cc3b3f3975c94b53400500432ad416bff00e52b545afadb6f2df45d92a`;
- independently implemented `reduce_source_admission.py`: `87,122` bytes, SHA-256
  `52d521e0215886183e04fb07f885047f032f6c413ed9fdf4d68a4148245e1edf`; and
- `test_source_admission_packet.py`: `107,738` bytes, SHA-256
  `42b798992a18ec3e7ec1d3c358b7953713194296540ce8c80e1f3c6920030478`.

Every member is a physical owner file at mode `0600`, link count one, in the physical owner-only
mode-`0700` packet root. Exact Python 3.14 `-I -B -S` tests pass `40/40`; pinned Ruff `0.15.20`
lint/format, AST, both contract parsers, the canonical manifest seal, path topology, final
verifier/R16 identities, and clean detached D16 all pass. The corrected known-bads prove red
process retention for malformed post-child receipts and terminal no-overwrite behavior when the
reducer parent-directory fsync fails. Same-packet validation is not independent acceptance.

An independent pre-preflight hostile audit rejected `r3` despite its green same-packet suite. Its
supervisor could block while opening a child-created FIFO before retaining a red process record;
`lexists`/`exists` absence gates could convert observation faults to absence; reducer parent-fsync
failure could leave a green-looking immutable calculation; reducer size was bounded only after
creation; exact-Git output was bounded only after `communicate()` buffered it; executing-code
identity was a basename tautology; reducer CLI resolution erased route aliases; and the suite did
not prove the top-level no-replay boundary for those post-child faults. No candidate, preflight,
packet acceptance, bind, replay, receipt, process record, reducer output, or final acceptance may
ever be attached to `r3`. Its bytes and empty ceremony/receipt roots remain retained untouched.

The only potentially eligible replacement is now the fresh one-shot materialization at
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r4`. Its packet manifest is
`2,931` bytes, SHA-256
`6ab39f2ae8ddfa2a8d0566878d1ad09de8ad36aebba626a9da85d1ff00166a6c`, payload SHA-256
`3202216895dc74c1ae87dcf7055763f3b395f4926a00cd862944075e76add562`. It binds:

- `contract.json`: `14,197` bytes, SHA-256
  `992def50f63e6841a376dadbc4d45899556d512351ff72d22df2e8d7ab148dca`;
- `CONTRACT.md`: `21,255` bytes, SHA-256
  `57719b53201d8f987a0909ffaee6299a1f2a0e004df150f16c336bdb44c415e8`;
- `supervise_source_admission.py`: `129,525` bytes, SHA-256
  `28774d3a7ecdf8d27a82554bbc4f751124b557579f7c5645fcd1f7b626c1dcd7`;
- independently implemented `reduce_source_admission.py`: `90,823` bytes, SHA-256
  `1f88c1f833fd7d77542f1e011a48e0f9167862f6d73e2ffe57b270d02556da63`; and
- `test_source_admission_packet.py`: `132,255` bytes, SHA-256
  `84d4c121d9ac0c2e629249fcb212ef73b1922ffc9fc87584d27a5eab5654dcf0`.

Every member is a physical owner file at mode `0600`, link count one, in the physical owner-only
mode-`0700` packet root. Exact Python 3.14 `-I -B -S` tests pass `48/48`; pinned Ruff `0.15.20`
lint/format, AST, both independent contract parsers, canonical manifest and payload replay, path
topology, verifier/R16 identities, and clean detached D16 pass. The corrected suite now proves
tri-state absence, nonblocking nonregular reads and races, bounded Git and environment capture,
actual executing-module identity, exact reducer CLI routes, pre-create reducer size rejection,
top-level no-replay, and a sealed provisional reducer artifact that never claims its later parent
fsync succeeded. Final source admission additionally requires a separately supervised reducer
invocation/process receipt under a future specification; it remains
`UNDER_SPECIFIED_PROHIBITED`. Same-packet validation is not independent acceptance.

Subsequent independent review rejected `r4`; the permission in the preceding historical
paragraph is withdrawn. A Ruff invocation from its detached D16 worktree created ignored
`.ruff_cache` entries. Its exact ignored-inclusive status stream is `78` bytes with SHA-256
`076e8f88c0965967983706468cc3714e6a9687450987e031fce49274d5828c33`, falsifying the clean-
worktree gate. Review also found that the active contract route was not bound to the manifest,
coherent path rebasing remained admissible, Git configuration/control state was incompletely
isolated and bound, the receipt-to-preflight source projection was incomplete, and reducer path,
freeze, and parent-descriptor checks were incomplete. `r4` remains retained without cleanup or
repair. Its ceremony and receipt roots are empty, and no candidate, preflight, packet acceptance,
bind, replay, v2 receipt, strict reduction, or final acceptance may be attached to it.

The next immutable replacement, `r5`, is also rejected and retained untouched. Its `3,758`-byte
manifest has SHA-256
`26e5f18dfbe24121fc9c10ec0092049b662f9f643e8ab0506c80ec116c3df861` and payload SHA-256
`a5442dafb427a2a32e77b439fbb6d65e0924f33fba4bc025c7aeebdda599d311`. Its exact immutable
Python 3.14 `-I -B -S` run passed `56/57` tests and failed only
`test_frozen_contract_is_accepted_by_both_independent_parsers`: that test correctly required a
mutable staging route to reject but incorrectly required the installed exact frozen route to
reject too. The exact route itself parsed correctly, but a packet whose frozen suite is red is
ineligible. Its ceremony and receipt roots remain empty; no candidate or ceremony artifact may
ever be attached to `r5`.

The only potentially eligible replacement is the fresh immutable materialization at
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r6`. Its canonical packet
manifest is `3,758` bytes, SHA-256
`087a6cb629d76cc22bf52ac81af332b581973bc836da6e1c6e761c6d59448b57`, with payload SHA-256
`21758412a19aa3b06e857689c8aa06ead690cb202dc99d2e1ac9c0831f492e7c`. It binds:

- `contract.json`: `15,033` bytes, SHA-256
  `b647d9cd3c6b689cd9fcbeebf67e1bce3ec102a9816758230faeee5da63ebe83`;
- `CONTRACT.md`: `32,121` bytes, SHA-256
  `2d7acd2055931c92ecc2ea0d7bcfff4e17e29edaeb2e9d6ef8045e8782330cb1`;
- independently implemented `reduce_source_admission.py`: `118,579` bytes, SHA-256
  `9a2957902da21b3417fd1cf282d19cd8af6afa318e5d58d456583d2b83383e5c`;
- `supervise_source_admission.py`: `174,479` bytes, SHA-256
  `41ea3dfd0e21594de4f7f539ee7faf01cbaab8f199ca1e246970c7a847bf5609`; and
- `test_source_admission_packet.py`: `162,624` bytes, SHA-256
  `0b94cf49335b40a0b26c88a43332db6017767d8a42933f280f39927be3b31c8c`.

Every packet artifact is a physical UID-`501`, mode-`0600`, link-count-one file in the exact
six-file inventory under a physical owner-only mode-`0700` packet root. The exact frozen Python
3.14.2 `-I -B -S` hostile suite passes `57/57`; pinned Ruff `0.15.20` lint and format checks pass
with `--no-cache`; both independent contract parsers, the canonical manifest and payload seal,
every member identity, the live bootstrap validator, and the supervisor plus independent-reducer
Git-layout checks pass. The detached worktree remains clean at D16
`355010c4b668c85fcd2647586c56d7a21b8b88d0`, tree
`9b4adcf6d368a3cc650899898b4d3316aa6a9ce8`; ignored-inclusive status is zero bytes and all
`2,631` index rows are normal. No cache, candidate, preflight, packet acceptance, bind, replay,
receipt, process record, reducer output, or final acceptance was created by this audit.

A separate read-only immutable audit reached the same result without changing any audited hash,
file identity, or directory inventory and found no remaining mechanism blocker. It independently
repeated the `57/57` suite, no-cache Ruff checks, exact-route parsing, pre-acceptance manifest
validation, bootstrap hashes, clean detached D16 observation, and live Git-row reduction. It also
confirmed that the ceremony and receipt roots were empty and that every reserved artifact was
absent. Its verdict is only `ELIGIBLE AS AN AUTHORITY-FALSE PRE-ACCEPTANCE CEREMONY PACKET`.

`r6` may therefore receive one fresh direct-D16 F17 candidate containing this controlling
amendment and at most one fresh authority-false preflight. Every old active path, manifest
identity, preflight identity, candidate identity, test count, and command below is historical
unless explicitly re-frozen to this `r6` namespace and identity. This correction changes no
scientific arm, schedule, outcome, estimand, missingness, stopping, multiplicity, resource, host,
GPU, publication, or Odeya authority.

This record is intended to enter Git atomically with the proposed F17 source. It therefore cannot
serve as independent preregistration evidence for code in that same commit. Its role is narrower:
freeze the candidate's claim, scope, rejection rules, publication topology, and limitations before
the candidate is materialized as the exact direct child of D16. Independent acceptance remains an
external operator decision over detached identities and retained replay evidence.

## Purpose and maximum claim

Generation 17 addresses one registered blocker: Sentinel's GitHub Actions lane did not bind a
complete, exact repository-local CI input surface or prove that the tested environment was freshly
installed from hash-locked, Python-minor-specific requirements. The proposed replacement freezes
and replays an enumerated workflow, two exact dependency locks, a fresh virtual-environment
installation contract, a strict pip-report/installed-metadata comparison, an isolated pytest
launcher, and hostile fixtures for the admitted policy.

The maximum licensed claim after a complete accepted publication is:

> Exact accepted F17 repository bytes define and replay the enumerated Generation-17 CI controls;
> separately retained Python 3.10 and 3.11 workflow jobs reported passing the frozen hash-locked
> install, pip-report, installed-metadata, and test checks in fresh job-local virtual environments
> at the cited commit.

That wording is conditional on exact accepted F17, R17, T17, and B17 identities plus separately
retained hosted-run identities. A green local or hosted command alone does not establish it.
Generation 17 does not establish a hermetic runner, upstream action or package authenticity,
deterministic lock solving, reproducible wheel building, an offline mirror, an SBOM, SLSA
conformance, whole-system reproducibility, safety, readiness, scientific correctness, or
authority.

## Frozen accepted base and candidate topology

The immutable accepted base chain is:

- D16 `355010c4b668c85fcd2647586c56d7a21b8b88d0`;
- B16 `737f1f2160134cf1e3d0d7216b21993848f06078`;
- T16 `b5536802b62acaab3a1b57f93618b74dee3c3312`;
- R16 `f417b77e1a8f5ca8d7c883fe41248e3e7c4f2666`;
- PIN16 `a5dc84c731c7272174c70b950ebc890b01330a3c`;
- F16 `51370ccac79fd141f774ca462a4fdd8b8f3f5b55`; and
- B15 `21509ef2cdb634c02fac9310b57b7608b9878530`.

R16's canonical tooling-receipt SHA-256 is
`31e851778869b46c75c1da78545aee469f48f3b6f54bd78d36d8d1c18422a391`.
The proposed F17 must be one single-parent direct child of exact D16. Its changed-path set must be
exactly the following 22 regular files, with no additional path:

1. `.github/workflows/ci.yml`;
2. `AGENTS.md`;
3. `docs/research/ITER135_GENERATION_SEVENTEEN_CI_HARDENING_PREREGISTRATION_2026-08-21.md`;
4. `experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py`;
5. `experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py`;
6. `pyproject.toml`;
7. `scripts/make_handoff.py`;
8. `scripts/mission_state.py`;
9. `tests/test_handoff_generator.py`;
10. `tests/test_iter135_ci_install_verifier.py`;
11. `tests/test_iter135_gen17_ci_hardening.py`;
12. `tests/test_iter135_launch_authorization.py`;
13. `tests/test_iter135_launcher.py`;
14. `tests/test_iter135_tooling_verifier.py`;
15. `tests/test_mission_state.py`;
16. `tools/ci/requirements-ci-py310.lock`;
17. `tools/ci/requirements-ci-py311.lock`;
18. `tools/ci/requirements-ci.in`;
19. `tools/ci/run_pytest_isolated.py`;
20. `tools/ci/supply-chain-manifest.json`;
21. `tools/ci/verify_ci_install.py`; and
22. `tools/ci/verify_supply_chain.py`.

The obsolete diagnostic path `tests/test_gen17_ci_hardening.py` must be absent from the candidate
tree. It was introduced only on the WIP child of D16 and is not a deletion from D16 itself.

After external source acceptance, the only admissible publication topology is:

1. F17: the exact source-only direct child of D16 described above;
2. R17: one receipt-only direct child of F17;
3. T17: one `MISSION_STATE.json`-only direct child of R17; and
4. B17: one `CONTINUITY.md` plus generated `HANDOFF.md` direct child of T17.

The fixed publication reason code is
`D16_CONTENT_ADDRESSED_CI_INSTALL_REPLAY_AND_NEXT_SOURCE_V2_BOOTSTRAP`. T17 must retain iteration
134 as the last completed experiment, retain the Iteration-135 scientific preregistration
unchanged, keep `run_state` exactly `UNKNOWN`, and advance only to
`LIFECYCLE_OBSERVER_REQUIRED`. T17 may authorize offline implementation and validation of the
actual observer and performing-controller contract. It may not create `IDLE`, run an observer,
contact a provider or host, prepare a host, create H/E/P/S, run smoke, use a GPU, or execute an
analytic episode. T17 must never be published as a standalone canonical tip.

## Exact CI input and workflow freeze

The strict canonical `tools/ci/supply-chain-manifest.json` at accepted F17 binds exactly its `12`
enumerated repository-local CI-control files, their byte counts and SHA-256 values, both parsed
lock projections, the exact direct requirements, and the critical workflow projection. It is not
the inventory of all 22 changed F17 paths or the whole tree; the accepted source commit and R17
receipt supply those broader content identities. Any co-edit of the 12-file set requires a new
manifest and new F17 candidate; the manifest is not independent of the commit that contains it.

The workflow freeze is:

- GitHub workflow ID exactly `304353015`, name exactly `ci`, and path exactly
  `.github/workflows/ci.yml`;
- acceptance event exactly `push`, run attempt exactly `1`, and the complete job set exactly
  `check (3.10)` and `check (3.11)`--no third, renamed, skipped, or missing job;
- one `check` job on `ubuntu-latest`, timeout 45 minutes, matrix fail-fast disabled;
- Python minors exactly `3.10` and `3.11`, each mapped to its distinct exact lock;
- repository permission only `contents: read`;
- checkout `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` with full history and
  `persist-credentials: false`;
- setup `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`;
- locale `C.UTF-8`, time zone UTC, `PYTHONHASHSEED=0`, and one thread for MKL, OpenBLAS, and OMP;
- offline repository-input verification under the runner's pre-setup standard-library Python,
  before any action-installed Python or dependency is admitted;
- a new absent path under physical `${RUNNER_TEMP}` for each virtual environment and pip report;
- `pip --isolated --force-reinstall --require-hashes --only-binary=:all: --no-deps` against the
  matrix lock, followed by `pip check`;
- separate strict comparison of the lock, pip report, physical virtual-environment route, and
  installed distribution metadata;
- Ruff from the admitted virtual environment;
- targeted hostile controls and the full suite through the launcher with user site excluded,
  plugin autoload disabled, empty `PYTHONPATH`, `PYTHONHASHSEED=0`, and the named inherited
  `PYTHONHOME`, `PYTHONOPTIMIZE`, `PYTEST_ADDOPTS`, and `PYTEST_PLUGINS` variables absent; and
- documentation validation through the admitted virtual-environment interpreter.

The direct versions are Ruff `0.15.20`, pytest `9.1.1`, NumPy `2.2.6` and scikit-learn `1.7.2`
for Python 3.10, and NumPy `2.4.6` and scikit-learn `1.9.0` for Python 3.11. Transitive rows and all
admitted archive hashes are governed by the two committed locks, not by a new index solve.

The workflow must reject an existing or symlinked runner-temp target, dependency resolution,
sdists, unadmitted or missing distributions, archive-hash drift, a direct-URL report row,
extras-bearing requirements, report/version drift, a site-packages route escaping through an
intermediate symlink, an external pytest import, the exact named pytest/Python environment and
configuration injections above, action or step reordering, conditional skipping, matrix/lock
drift, mutable action references, and any
repository-local byte drift covered by the manifest.

## Next-source v2 bootstrap freeze

The published Generation-16 v1 binder is preserved byte-for-byte as historical behavior and must
not be used for F17. It models F16/PIN16 and requires a B16-rooted shape that cannot admit a direct
D16 child. Generation 17 instead proposes `sentinel.next_source_binding.v2`.

Before v2 executes, the operator must independently select an external directory containing the
exact proposed next-source-v2 verifier at its canonical relative path and measure its SHA-256. The
final detached verifier is
`experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py`, exactly `297,539`
bytes with SHA-256
`4c73ba1c83348a51ea860a88c9b18ed057f391a829882960030b7d68d144451d`. This is distinct from
`tools/ci/verify_supply_chain.py`, whose identity is carried by the 12-file supply manifest.
Executing code cannot authenticate its own pre-execution selection, so the
external root, digest, exact R16 receipt digest, interpreter selection, and Git selection are
bootstrap trust axioms.

V2 may run only from a clean physical worktree detached at exact D16. It must use isolated,
no-bytecode, no-site Python; authenticate the exact R16 receipt; require the R16-bound Python and
Git physical canonical paths, regular executable modes, byte counts, SHA-256 values, and version
strings; and hold the complete live file identities stable across two separate complete passes.
Historical device, inode, and timestamps are deliberately not portable acceptance fields across
filesystem mount epochs. The R16-bound Python standard-library installation remains an external
axiom.

Each of the two separate passes must parse and SHA-verify raw Git commit, tree, and blob objects
for the exact D16-to-B15 chain and the proposed direct child. It may not check out, import, or
execute F17.
The complete candidate regular-file manifest, commit object, tree, unique blobs, path scope, and
candidate verifier byte equality with the detached external verifier must match across both
passes. The output is canonical, deterministic, bounded, atomic no-clobber evidence with both
publication and launch authority exactly false.

The v2 receipt must be separately replayed and independently accepted before F17 is checked out,
imported, executed, pushed, or used to advance a generation. Producer review, a model signature,
receipt self-checksum, or agreement between two executions is not independent acceptance.

The v2 receipt is an external source-admission artifact, not R17. Its verifier root and canonical
receipt must be retained outside both the Sentinel worktree and common Git directory under
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/`, with detached byte count and
SHA-256 recorded in the canonical handoff. R17 is the later repository artifact
`experiments/iter135_neuroncap_blind_braking_dose_response/tooling_verification_receipt.json`, a
different schema generated only after exact F17 is independently admitted, executed, and
canonically published. Neither artifact may substitute for the other.

The source-admission execution paths are frozen exactly as follows:

- external base:
  `/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3`;
- accepted verifier root:
  `/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/verifier-root`;
- accepted verifier file:
  `/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/verifier-root/experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py`;
- clean detached D16 worktree and process working directory:
  `/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/d16-detached-worktree`;
- no-clobber v2 receipt:
  `/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/receipts/f17-next-source-v2.json`;
  and
- exact R16-bound interpreter:
  `/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/bin/python3.14`.

Both bind and replay must be created with process umask exactly `077` and an `execve` environment
assignment containing exactly these eight keys and no others:

```text
LANG=C
LC_ALL=C
PATH=/opt/homebrew/bin:/bin:/opt/homebrew/Cellar/shellcheck/0.11.0/bin:/opt/homebrew/Cellar/ruff/0.15.20/bin:/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/bin:/opt/homebrew/Cellar/git/2.48.1/bin:/usr/bin:/usr/sbin:/sbin
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
PYTHONDONTWRITEBYTECODE=1
PYTHONHASHSEED=0
PYTHONNOUSERSITE=1
TZ=UTC
```

A hostile pre-execution test found that the frozen macOS CPython 3.14.2 adds
`__CF_USER_TEXT_ENCODING=0x1F5:0:0` before Python code can observe `os.environ`, even when the
interpreter is launched through `/usr/bin/env -i` and even when a different value is explicitly
assigned. The launch assignment therefore remains the exact eight-key vector above, while the
effective Python environment is separately frozen as those eight keys plus that exact ninth
key/value. The supervisor and an exact isolated child probe must record both maps and reject every
other key or value. No surface may describe the effective environment as eight keys. This
machine/platform observation is not a cross-platform environment or reproducibility claim.

The verifier root, detached worktree, receipt directory, and Sentinel common Git directory must be
physically distinct in the manner enforced by v2; the receipt may not be inside the verifier
root, worktree, or common Git directory. The persistent external base, verifier-root, and receipt
directories must be owned by the executing user and materialized with mode `0700`; the no-clobber
receipt must remain the verifier-created regular file at mode `0600`. The external directories and
verifier bytes must be materialized and operator-inspected before either invocation. With the
process working directory fixed to the D16 worktree above, the exact bind argv template is:

```text
[
  "/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/bin/python3.14",
  "-I", "-B", "-S",
  "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/verifier-root/experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py",
  "--bind-next-source-v2", "<F17_COMMIT>",
  "--accepted-tooling-receipt-sha256", "31e851778869b46c75c1da78545aee469f48f3b6f54bd78d36d8d1c18422a391",
  "--accepted-v2-verifier-root", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/verifier-root",
  "--accepted-v2-verifier-sha256", "4c73ba1c83348a51ea860a88c9b18ed057f391a829882960030b7d68d144451d",
  "--next-source-v2-repository-root", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/d16-detached-worktree",
  "--next-source-output", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/receipts/f17-next-source-v2.json"
]
```

The exact replay argv template, from that same working directory, is:

```text
[
  "/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/bin/python3.14",
  "-I", "-B", "-S",
  "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/verifier-root/experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py",
  "--verify-next-source-binding-v2", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/receipts/f17-next-source-v2.json",
  "--accepted-tooling-receipt-sha256", "31e851778869b46c75c1da78545aee469f48f3b6f54bd78d36d8d1c18422a391",
  "--accepted-v2-verifier-root", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/verifier-root",
  "--accepted-v2-verifier-sha256", "4c73ba1c83348a51ea860a88c9b18ed057f391a829882960030b7d68d144451d",
  "--next-source-v2-repository-root", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/d16-detached-worktree",
  "--expected-candidate-commit", "<F17_COMMIT>",
  "--expected-binding-sha256", "<F17_BINDING_SHA256>"
]
```

Only `<F17_COMMIT>` and the SHA-256 of the once-produced canonical receipt bytes,
`<F17_BINDING_SHA256>`, are post-materialization substitutions. They must be inserted as individual
argv elements without shell evaluation. Any other argv, path, interpreter, working-directory,
outer environment, umask, or receipt-output change creates a different, unaccepted ceremony.

The external retained ceremony namespace is also fixed now:

- `ceremony/preflight.json`;
- `ceremony/bind.stdout.bin`, `ceremony/bind.stderr.bin`, and `ceremony/bind.process.json`;
- `ceremony/replay.stdout.bin`, `ceremony/replay.stderr.bin`, and
  `ceremony/replay.process.json`;
- `ceremony/strict-reducer.json`; and
- `ceremony/operator-acceptance.json`.

Every path is relative to the external base, must be absent before its one creation, and must be a
physical owner-only regular file at mode `0600`; the `ceremony` directory must be physical,
owner-only, and mode `0700`. No file may be overwritten, truncated, selected around, or deleted
after a failed or successful attempt.

The previously missing schema, recorder, capture, timeout/signal, reducer, and acceptance
contracts are now frozen in one proposed external packet at
`/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/ceremony-packet`. The packet is
materialized but not independently accepted and grants no authority. Its canonical manifest is
`2,640` bytes, SHA-256
`82c25835a75f02c97f27ac13a81f0db4775278d7a66a3c19a699046f4dffd81c`, with payload SHA-256
`233f17490242e9d19ecd13318ce4c8201598dc17c63d0548e7e0f751b9bdc5cb`. It binds:

- `contract.json`: `13,790` bytes, SHA-256
  `bb994dba02ba7079cd47bcfba212844da31db8b59a93a84bbe91e077977c694f`;
- `CONTRACT.md`: `16,219` bytes, SHA-256
  `71119ce06f5bf80c839bb5de726f6ba66dbfe4cbde02666c6eb29819e3098792`;
- `supervise_source_admission.py`: `121,753` bytes, SHA-256
  `68dbb3cc3b3f3975c94b53400500432ad416bff00e52b545afadb6f2df45d92a`;
- independently implemented `reduce_source_admission.py`: `87,122` bytes, SHA-256
  `52d521e0215886183e04fb07f885047f032f6c413ed9fdf4d68a4148245e1edf`; and
- `test_source_admission_packet.py`: `107,738` bytes, SHA-256
  `42b798992a18ec3e7ec1d3c358b7953713194296540ce8c80e1f3c6920030478`.

All packet files are physical owner files at mode `0600`; the packet directory is physical
owner-only mode `0700`. The schemas are
`sentinel.next_source_ceremony_packet.v1`,
`sentinel.next_source_ceremony_packet_acceptance.v1`,
`sentinel.next_source_ceremony_preflight.v1`,
`sentinel.next_source_ceremony_process.v1`,
`sentinel.next_source_ceremony_reducer.v1`, and
`sentinel.next_source_ceremony_operator_acceptance.v1`. Generated retained control JSON is
canonical and forbids duplicate keys, floats, nonfinite values, Boolean integer aliases,
extra/missing fields, noncanonical encoding, and payload-checksum drift. The manifest-bound
`contract.json` is the one explicit exception: both parsers require the same strict typed object
but preserve its human-readable, intentionally noncanonical encoding. Binary streams are retained
without text decoding.

The one-shot supervisor requires the exact packet-manifest, preflight, and independent pre-bind
operator-assertion SHA-256 values as detached inputs. Preflight binds the clean detached D16
commit/tree, raw candidate commit bytes/SHA-256, sole parent, tree and exact 22 changed paths,
full packet inventory, verifier/R16/Python/Git identities, exact eight-key launch assignment,
exact one-key macOS CPython addition and nine-key effective environment, cwd, umask, and absence
of every reserved output. It does not check out, import, or execute the candidate. A red
preflight is terminal for that candidate.

Each child stage has one `2,400`-second monotonic wall deadline beginning before spawn, a
`60`-second process-group `SIGTERM` grace, process-group `SIGKILL` if required, a `10`-second reap
bound, and a `5`-second post-main-exit pipe-EOF bound. Each stdout and stderr stream has a
`65,536`-byte retained limit; the v2 receipt limit is `16,777,216` bytes. Streams are opened
before spawn with `O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0600`, drained concurrently as binary,
fsynced, hashed, and described in no-clobber process records. Nonzero/negative exit, timeout,
signal, overflow, missing EOF, receipt ambiguity, spawn/recorder fault, missing artifact, or
unexpected byte is terminal rejection; no replay follows a rejected bind and no failed artifact
is deleted or retried away.

Before bind, a separately identified human must create a canonical no-clobber
`ceremony-packet/operator-packet-acceptance.json` over the exact packet, preflight, candidate and
bootstrap identities. Its decision is exactly `AUTHORIZE_EXACT_F17_BIND_AND_REPLAY_ONLY`; only
bind and replay authority are true. The typed human assertion is explicitly an external trust
axiom, not cryptographic identity authentication. A producer, model, subagent, checksum, test,
supervisor, reducer, receipt or repeated execution cannot create that acceptance. After a green
independent reducer, final source admission remains `UNDER_SPECIFIED_PROHIBITED`. This packet does
not authorize creation of `ceremony/operator-acceptance.json`; a separately reviewed
pre-creation contract must first freeze its schema and exact bindings, independent-human
authentication and chronology, no-clobber authoring/readback procedure, bounded checkout and
local-validation resource envelope, separate read-only validator, and retained known-bads.
Neither executable creates either operator assertion.

The exact R16-bound Python 3.14 `-I -B -S` hostile suite passed `40/40` tests. It covers canonical
parsing, packet/inventory/path/mode/hash drift, no-clobber/no-follow writes, assigned/effective
environment and command drift, acceptance binding, harmless child success, nonzero/signal,
timeout, overflow, binary and invalid-UTF-8 streams, leaked pipe EOF, exact bind/replay bytes,
receipt candidate/tree/payload/authority drift, post-child receipt symlink/link/mode/oversize
faults with retained red process evidence, reducer parent-directory fsync failure, and red
evidence that cannot be overwritten or retried. It discovered and caused the pre-evidence macOS
environment correction above and a
shape-only verifier-hash false acceptance in the first supervisor draft. Same-packet tests and
producer review are not independent acceptance; no active same-UID attacker was simulated.

No `preflight.json`, packet acceptance, v2 receipt, process record, reducer output, or final
operator acceptance exists yet. The manifest and packet close the specification omission, but
independent packet/preflight/candidate selection remains a hard pre-bind blocker. The receipt
alone, a green packet test, this prerecord, or this handoff cannot substitute for it.

After the final F17 object is materialized, the first one-shot executable is the preflight, not
the binder. From the exact D16 cwd under umask `077` and the eight-key assignment above, its argv
template is exactly:

```text
[
  "/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/bin/python3.14",
  "-I", "-B", "-S",
  "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/ceremony-packet/supervise_source_admission.py",
  "--contract", "/Users/danielwahnich/sentinel-bootstrap-evidence/gen17-20260822-r3/ceremony-packet/contract.json",
  "preflight",
  "--candidate-commit", "<F17_COMMIT>",
  "--accepted-packet-manifest-sha256", "82c25835a75f02c97f27ac13a81f0db4775278d7a66a3c19a699046f4dffd81c"
]
```

Only `<F17_COMMIT>` is substituted. Preflight is permitted before the human assertion because it
creates the exact candidate-bound record that must be inspected. The later `run` mode is
prohibited until an independent operator supplies detached accepted SHA-256 values for this
manifest, that green preflight, and the exact canonical packet-acceptance assertion.

## Publication evidence, missingness, stopping, and multiplicity

No hosted run is inherited from the diagnostic WIP. Every disposable run must use a fresh unique
non-PR branch, and every canonical run must use exact `master`. At the time of each push, no pull
request may be open from the disposable branch. The only admitted event is workflow
`304353015` / `ci` / `.github/workflows/ci.yml`, event `push`, attempt `1`, with exactly
`check (3.10)` and `check (3.11)`. A `pull_request`, manual/API dispatch, rerun, second disposable
branch for the same stage, duplicate event, or any other extra run at the same candidate identity
is a retained deviation and rejects that candidate, even if green; it may not be discarded or
selected around.

After v2 source acceptance, exact F17 must receive its one fresh disposable-branch run with both
Python jobs present at exact F17 and all frozen steps green. A missing job, cancelled job, skipped
required step, stale SHA, missing logs/metadata, indeterminate conclusion, or absent independent
readback is missing evidence—not a pass. Any red or incomplete run rejects that exact candidate;
do not rerun it to search for a green attempt. A correction is a new candidate with a new object
identity and fresh binding.

Only a green accepted disposable result permits the same exact F17 to fast-forward canonical
`master`. A distinct canonical two-job attempt-1 run at exact F17 must then pass before R17 is
generated. R17 is generated once from a clean canonical F17 by the committed Generation-17
receipt generator using the exact command contract it serializes, then committed alone,
independently replayed, and validated on both a fresh disposable receipt lane and canonical
`master`. The exact physical Python executable, process working directory, complete outer
generator argv, and complete sanitized environment for this post-F17 R17 generation are not yet
frozen and cannot be inferred from an unaccepted F17 toolchain. This is a pre-execution blocker,
not a discretionary blank: after F17 acceptance and before any R17 generator process starts, a
separate retained ceremony packet must bind all four fields to the accepted F17 identities. No
placeholder command, current ambient Python, inherited shell environment, or guessed default
output is admissible. No failed generator is retried under the same candidate.

T17 and B17 are then constructed locally as one inseparable state/baton pair. B17 receives one
fresh disposable run while canonical upstream remains exact R17; only a green exact result permits
one atomic fast-forward through T17 to B17, followed by a distinct canonical green run. T17 is
never a standalone upstream tip. Any topology, byte, receipt, phase, generated-handoff, or upstream
drift stops publication.

These jobs are acceptance gates, not repeated scientific trials. There is no averaging, best-of
selection, majority vote, or multiplicity rescue. Every required lane is an intersection: one
missing or failed required result makes the stage unaccepted. Failures, diagnostics, candidate
objects, branch identities, and run identities must be retained with the same visibility as green
evidence.

## Required independent verification and falsifiers

Independent verification must include all of the following before acceptance:

1. detached hashing of the external v2 verifier and exact R16 receipt before execution;
2. two complete v2 raw-object replays from clean detached D16 and exact receipt-byte equality;
3. a separately invoked strict parser/replay reducer for the v2 receipt and candidate manifest,
   with external operator acceptance still required because it shares the proposed verifier
   implementation;
4. repository-local supply replay under both available Python 3.10 and 3.11 standard-library
   interpreters;
5. fresh virtual-environment installation and installed-state verification in each hosted lane;
6. exact source, receipt, state, baton, upstream, and receipt-history topology checks; and
7. independent readback of every required hosted run's event, attempt, commit, job set, conclusion,
   timing, and frozen workflow identity.

Required retained known-bads include: duplicate/noncanonical manifest JSON; repository byte drift;
action, runner, matrix, lock, step-order, command, permission, timeout, environment, or conditional
drift; quoted, escaped, tagged, anchored, explicit, or flow YAML mapping keys that could obscure a
control field; missing hash enforcement; dependency resolution; sdist admission; pip-report hash,
version, requested/direct/extras, or installed-inventory drift; extra/missing distributions;
Python-minor mismatch; user-site, plugin-autoload, named pytest/Python environment, configured
pytest, or path injection within the exact frozen launcher boundary; intermediate virtual-environment
route symlinks; external pytest import; candidate parent/scope/path/mode/verifier drift; malformed
or duplicate v2 receipt fields; accepted-chain or tool drift; single-pass substitution; output
collision; and F17/R17/T17/B17 topology, phase, or upstream drift.

Any such finding falsifies Generation-17 acceptance. It does not weaken a scientific null, create
launch authority, or permit a broader claim.

## Resource and authority boundary

Generation 17 has an exact GPU budget of `0 GPU-hours` and an exact analytic-episode budget of
`0`. One accepted-candidate ceremony has at most six workflow runs (F17 disposable/canonical, R17
disposable/canonical, and B17 disposable/canonical), each with exactly two jobs and a 45-minute
job timeout: at most `12` jobs and `540` aggregate job-minutes. The `540` job-minute value is a
hard acceptance ceiling, not spending authority, quota, a reservation, or permission to create
even the first hosted event. Each hosted publication ceremony requires its own prior explicit
operator authorization for the external effect and repository publication plus a contemporaneous
billing/quota confirmation. Any failed, missing, duplicate, rerun, or extra stage stops; a
replacement candidate needs a new identity, new authorization, and separately recorded budget
rather than a rerun. No exact local CPU, RAM, or storage bound is claimed for repository-local
validation. Generation 17 must not use the available Google Cloud login, contact the
iteration-135 provider or host, inventory the remote filesystem, query lifecycle state, touch a
container or GPU, create H/E/P/S, run smoke, execute an episode, run an outcome analyzer, publish a
scientific result, change external repository settings, alter GitHub visibility, branch
protection, collaborators, or other hosted governance, or claim Odeya integration. The local
`AGENTS.md` added within F17 is a content-bound repository instruction candidate only; it does not
change external governance or grant publication, spending, host, provider, lifecycle, GPU,
experiment, or scientific authority.

The mutable `ubuntu-latest` image, Python patch releases, bootstrap pip, package index, network,
action provenance, and upstream archives are not content-addressed by this record. A hosted green
run is evidence only for the exact observed run and frozen repository inputs. It cannot prove that
another run would reproduce or that an upstream artifact is authentic. The pip report and
installed inventory are checked inside each job but are not uploaded or retained as row-level
canonical artifacts; external readback can establish that the frozen check reported success, not
independently replay the ephemeral installation. Installed distribution file bytes are not
rehashed; the control compares the pip-reported admitted archive hash and installed
name/version inventory.

After accepted B17, Sentinel remains scientifically at Iteration 134 with semantic attribution
`UNRESOLVED`, HUGSIM transfer `TRANSFER_NULL`, production readiness `NOT_ESTABLISHED`, and
Iteration 135 unexecuted. The next lawful work is offline construction of a source-bound lifecycle
observer and performing-controller contract. Odeya remains an architecture foundation and may not
be represented as an implemented Sentinel research engine.
