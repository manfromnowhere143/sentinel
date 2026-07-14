# Iteration 100 - HUGSIM structural expansion support audit

Verdict: `HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL`

## Summary

- `broad_committed_transfer_pairs`: `104`
- `broad_on_collision_pairs`: `92`
- `monitor_side_supported_pairs`: `77`
- `collision_actor_supported_pairs`: `0`
- `collision_actor_not_logged_pairs`: `104`
- `actor_match_audit_rows`: `8`
- `actor_match_structural_rows`: `5`
- `structural_bridge_covered_rows`: `5`
- `larger_committed_pool_exists`: `True`
- `can_expand_from_committed_reports`: `False`
- `new_instrumentation_required_for_larger_structural_bridge`: `True`

## Event

- `row_label`: `expansion_boundary_no_collision_actor_support`
- `measurements`: `{'broad_committed_transfer_pairs': 104, 'broad_on_collision_pairs': 92, 'monitor_side_supported_pairs': 77, 'monitor_provenance_counts': {'ambiguous_cpa_object': 0, 'ambiguous_ttc_object': 0, 'argmin_reconstruction_failed': 0, 'both_distinct_objects': 1, 'no_fire': 27, 'schema_unsupported': 0, 'unique_both_same_object': 0, 'unique_cpa_object': 36, 'unique_ttc_object': 40}, 'collision_actor_supported_pairs': 0, 'collision_actor_not_logged_pairs': 104, 'on_collision_collision_actor_supported_pairs': 0, 'on_collision_collision_actor_not_logged_pairs': 92, 'collision_actor_identity_fields': [], 'actor_match_audit_rows': 8, 'actor_match_classifiable_foreground_rows': 3, 'actor_match_structural_rows': 5, 'structural_bridge_covered_rows': 5, 'structural_bridge_compatible_rows': 5, 'larger_committed_pool_exists': True, 'can_expand_from_committed_reports': False, 'new_instrumentation_required_for_larger_structural_bridge': True}`

## Boundary

report-level expansion-support boundary only; no actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, retuning, or approval-to-run claim
