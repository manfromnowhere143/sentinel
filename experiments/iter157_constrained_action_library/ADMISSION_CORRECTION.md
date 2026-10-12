# Iter157 admission inventory correction

12 October 2026. **Post-evidence administrative correction, not a new preregistration.**
The producer completed once. Its 75 retained rows report 61 prior-constraint
failures and 14 background rejections. These are producer diagnostics until
independent admission. The first checker failed before any scalar query because
the registered `source_files` included `_classes.py` and `_ops.py`. The inventory
builder had treated PyTorch's synthetic module `__file__` values as filesystem
paths relative to the repository. Neither path exists in the frozen Git tree or
workspace. No scientific source was missing; these were nonexistent extra entries.

Retain the original PLAN, producer, checker, raw commit, stderr and failed receipt
unchanged. A separately frozen corrected checker removes exactly these two
non-repository references from the source-inventory comparison. It still compares
the original PLAN bytes and hash, all 38 real source paths, the complete raw
inventory, input identities, population, masks, controls, progress and ranking.
Its scientific statements and numeric operations must be AST-identical to the
original checker apart from importing the corrected source-inventory wrapper.
The wrapper is itself bound to the new correction commit. No arbitrary missing
file may be omitted. No source hash, mask, count, threshold or action changes.

No producer retry, new action query or driving episode is authorized here. Run
one corrected admission into the previously nonexistent admission path after
committing this correction, using a distinct stdout/stderr/receipt. Keep the
original failed attempt visible. This corrects an administrative admission
inventory after producer data were observed; a final result must disclose that
scope. It does not retroactively turn the first checker into a pass or establish
that the original plan was executable unchanged.

The added qualification checks reject an altered removal set, original plan hash,
nonexistent real source, untracked source, source drift and a different checker
algorithm. They also validate the actual frozen inventory prospectively, which
the first qualification omitted. The no-query repeat rule and scalar scientific
coverage remain as registered in PROTOCOL.
