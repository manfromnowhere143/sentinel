# Independent audit of Iteration 137 numbers

The retrospective stdlib recount agrees with the reported 912 calls, all four groups of 228,
all exact numerical repeats, all 114 cases with varying timed final control, and every reported
nearest-rank latency/iteration quantile. No numerical correction was required. See
[the arithmetic audit](proof/audit137.stdout) and [audit source](audit137.py).

The evidential units deserve stricter wording: **114 scheduled typed cases represent 112 unique
typed input records**, derived from 57 dependent decisions in one previously inspected driving
case. The original protocol intentionally retained duplicate inputs. The repeated calls measure
execution stability; they do not increase the number of independent driving scenarios or establish
population safety. The [duplicate-count receipt](proof/unique_inputs_audit.json) and retained
script expose that denominator.

The 50 ms value comes from the solver's configured loop budget and the registered engineering
comparison threshold. A vehicle's admissible end-to-end latency was not established. Adapter
timing includes input conversion and diagnostic record/digest construction. It is not pure
optimization time, uninstrumented controller time or physical actuation latency. Even after
that distinction, the **full solver** exceeded 50 ms on 38/228 idle calls in each mode and on
228/228 contended calls in each mode. Diagnostic logging alone does not explain all misses.

The CPU result supports the next controlled question: whether the explicit numerical execution
mode yields matching full live traces. It supplies no evidence that an additional signal helps,
that braking is useful, or that private industrial systems have been surpassed. Those require
separate outcome comparisons against strong responsive baselines, independent scenes and resource
constraints. A useful research program must survive these distinctions in its own reporting.
