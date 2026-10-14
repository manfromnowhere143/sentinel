# Iter165: discarded braking does not rescue this continuation method

**Contradicted.** None of the **25 discarded maximum-braking roots** yields a
complete exact/24 continuation within its frozen budget. The **24 retained roots**
also yield no completion. All 49 beams empty; no run exhausts its 60,000-attempt or
1,800-second cap. All scheduled runs execute; none is censored or retried.

| Population at absolute frame 27 | Runs | Complete paths | Attempts | First empty beam |
| --- | ---: | ---: | ---: | --- |
| Discarded two-step maximum braking | 25 | 0 | 59,690 | 8.00–10.25 s |
| Retained by the original beam | 24 | 0 | 24,328 | 7.50–8.50 s |

Across the schedule: **84,018 attempts and 39,584 search queries**. Every root uses
the same absolute 401-action horizon, original 7.75/9.00-second checkpoints,
controls, geometry and full 276,519-center background population. There are zero
grouping removals and 34,231 width removals in these new searches. Those counts
alone do not establish why a complete path was not found.

Independent admission checks **all 1,537 selected joined states and full masks**,
including each complete historical prefix and selected continuation. A separate
scalar classifier evaluates 250 distinct box geometries against the bound point
population: **69,129,750 point-state classifications**. Another 1,287 checks reuse
only that checker's exact previously computed geometry/population result. No
producer classification enters that cache. Motion and other physical constraints
are checked at every state, including reused boxes.

The selected paths end between 7.25 and 8.00 seconds. Eighteen reach the first
checkpoint; none reaches the second. An unobserved checkpoint is not a pass.
Search-log empty-beam time is not the end time of the chosen partial path.
Unselected physical rejection labels remain producer evidence.

This rules out completion by **this fixed continuation method on this finite root
population and budget**. It does not rule out other continuations, prove the source
state infeasible, show that pruning caused the original miss, or demonstrate native
recovery or superiority. The additional offline work is not an efficiency gain.

Source `ca2d517ed95a2f5d2858609f7e7c782a09972898`; raw
`0d8fa01dd6fc53942d1859c532c685c36cc7ffa2` committed before separate admission.
Producer 746.912 seconds; checker 444.361 seconds. Peak RSS stays below 630 MB;
all resource limits pass, both processes are reaped. The missing-output-parent
preinitialization failure is retained separately; no scientific acquisition had
initialized. No native driving, GPU, provider use or spending.
