# Iter190 — the left bend has unexploited full continuations

28 October 2026. **Supported:** all four retained left-bend late node records
have a separately verified full continuation within their original remaining
budgets. Three received no outgoing request in Iter189. The fourth received
requests, but none generated the complete admitted continuation. This answers
the conditional feasibility question; the integrated planner still completes 3/4.

The frozen population covers all **22 native nodes at frames 24–31**, representing
21 exact case/state/frame roots. Nodes 76 and 85 on the left bend share one root;
their distinct histories and original work remain visible. Both fixed arms ran
on every distinct root, with the smaller remaining allowance used for duplicates.

| Case | Node records / exact roots | Full-route roots | Checkpoint-only roots | Neither witness | Unrequested complete records |
|---|---:|---:|---:|---:|---:|
| Left bend | 4 / 3 | 3 | 0 | 0 | 3 |
| Right bend | 1 / 1 | 1 | 0 | 0 | 0 |
| Left chicane | 3 / 3 | 1 | 1 | 1 | 1 |
| Right chicane | 14 / 14 | 11 | 0 | 3 | 4 |
| Total | 22 / 21 | **16** | **1** | **4** | **8** |

There are 17 complete node records after counting both duplicate histories.
No arm is censored and neither necessary bound excludes a root. Four roots remain
bounded misses and one has only a checkpoint witness. Those five roots are not
proved incapable of full completion. Counts describe this exposed, dependent
population, not independent trials or a general success rate.

![Every retained late node, both arms and original requests](proof/late-continuations.png)

## The missed case: sufficient budget, available controls

The first stop/wait/route program completes from every left-bend root. It holds
steering while braking to zero, waits through absolute frame 32, then resumes
the frozen route controller at a target speed of 2 m/s. Completion occurs at
frame 33. Every original prefix and joined suffix passes separate scalar replay.

| Left node | Start frame | Original requests / evaluations | Attempts remaining | Conditional attempts | Original + conditional attempts | Charged conditional wall |
|---|---:|---:|---:|---:|---:|---:|
| 62 | 25 | 3 / 50 | 4,703 | 8 | 13,305 | 0.015735 s |
| 76 | 26 | 0 / 0 | 2,657 | 7 | 15,350 | 0.015202 s |
| 85 | 26 | 0 / 0 | 1,121 | 7 | 16,886 | 0.015202 s |
| 90 | 26 | 0 / 0 | 225 | 7 | 17,782 | 0.014419 s |

Each total stays below 18,000 attempts. Conservatively charging the entire
original left search wall, 23.190546 seconds, puts each conditional total below
23.207 seconds, within the original 120-second ceiling. These are alternative
conditional continuations. They do not claim that running all audit arms fits
inside one original search. Offline admission is separate work, and these wall
observations are not sensing-to-actuation latency or a paired speedup estimate.

At speed 0.125 m/s, a 0.25-second step reaches zero with acceleration
`-v/dt = -0.5 m/s²`. The bound old beam's fixed acceleration grid omits this
value; its three route commands also do not supply that braking action at these
states. Its left-bend searches exhaust their surviving beams after 330, 90 and
90 attempts, with control-bound and premature-completion rejections. The new
finite family supplies a valid stop without relaxing any tolerance or inventing
a negative-speed state. This is a concrete proposal difference, not a proof
that every other schedule is impossible or that search allocation is the sole cause.

Node 62's original outgoing evaluations match **one step** of the admitted
continuation; no original registered descendant matches that first step, and
the full continuation was neither generated nor registered. Nodes 76, 85 and
90 have no outgoing request. Thus there is direct evidence of unexpanded feasible
nodes and an already-requested node whose complete opportunity was not generated.
Changing nearest-neighbor weighting alone is not yet justified by these data.

## Complete admission and resources

The two fixed arms admit **16/21 full-route roots** for stop/wait/route and
**10/21** for beam then route. Every beam completion is also completed by the
other family. Equal ceilings do not equal matched work, and exposed-root counts
do not establish method superiority. The first checkpoint witness is the only
beam state receiving the fixed full-route suffix, as preregistered.

Independent reconstruction and replay check all **691 original outgoing
evaluations**, **10,524 new attempted transitions**, **7,487 new collision queries**,
and the complete union of **7,172 distinct queried states / 55,967,340 scalar
point-state classifications**, including rejected and unselected work. Full
native ancestry, original consumed attempts, exact clocks, controls, mask
inventories, program order, query counts and both necessary bounds are checked.

| Retained stage | Commit | Elapsed / peak RSS |
|---|---|---|
| Population freeze | `d33ee2570705fdd85449a69de6b0079200684600` | Before new suffix evaluation |
| Qualified source; 976 source/input bindings | `3722cb4cb87cb92d3b3ee85166acaef3a430811d` | Before acquisition |
| Sole raw acquisition | `85543d8d0cb673a9a4c2f9758f3702fccb50a6e1` | 26.105 s / 395,673,600 bytes |
| Independent admission | `549239cea5cb6e026f071396c345fb00745d1243` | 436.201 s / 466,796,544 bytes |

Raw was committed before replay. Both supervised processes exited and were reaped
within their registered resources; no scientific retry occurred. Qualification
passes 58 new tests and 238 focused regressions; 30 older native-library controls
were skipped because that library was not supplied to this test command. This
audit executes no native planner. Three retained successful paths / 106 states
receive scalar qualification replay, including 24 late timing controls. The
[qualification record](QUALIFICATION.json) retains logs and pre-freeze corrections.
Runtime is the bound local macOS Python 3.14.2 stack; hosted software CI is separate.

No new integrated search, simulator driving, GPU use or provider spending occurred.
The original four-case result remains 3/4 and source comparison stays closed.
Actual first-fire recovery, physical safety, information advantage, transfer,
measured response delay and competitor superiority remain unestablished.

[Protocol](PROTOCOL.md) · [admission](proof/admission.json) · [state](STATE.json) ·
[complete descriptive data](proof/descriptive.json) · [figure data](proof/figure-data.json) ·
[separate checker](check.py) · [primary research](RESEARCH.md) · [decision](DECISION.md).
