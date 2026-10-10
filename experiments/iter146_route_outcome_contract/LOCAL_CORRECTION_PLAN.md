# Local corrections after GPU qualification

2026-10-10. This record is prospective for code changes, after reviewing the frozen
source and before using the proposed witness comparator for any study inference.
It does not alter the eight-case GPU population, its source or its pass criteria.

1. Version the runner summary timing schema. Retain the original loop-work interval
   and add explicit elapsed-clock boundaries spanning the final guard and stop
   decision. Check interval nesting and ordering independently. Demonstrate the old
   failure with a synthetic 200-second post-step guard delay; do not rewrite v1 raw.
2. Preserve unknowns throughout paired witness and harm logic. Python all([None,
   None]) currently returns False, and a censored nominal can currently become a
   false no-harm label. A censored intervention can also become a false no-witness
   label through completion_qualified=False. Use explicit three-valued conjunction
   and distinguish observed failure from incomplete execution. An unobserved end
   of a pulse cannot certify absent action contrast. Keep the same successful
   completion criterion, prefix, action law and progress margin.
3. Exercise positive witnesses, separate comparators, intersection, observed harm,
   no contrast, inadequate progress, earlier completion and missing/censored
   branches with constructed truth-table reports. These are comparator unit
   fixtures, not new vehicle outcomes. Retain known-bad failures before fixing.

The original 64 pre-GPU tests and frozen GPU source remain separately identified.
New source receives local qualification only; no new GPU execution is inferred.
The full study still needs an executable finite launcher, full-horizon GPU runtime
calibration, active-monitor/nonempty-actor coverage and fresh resource binding.
