# A cell winner is not always retained in the beam

This inspection was performed after Iter160 admission on 12 October 2026. It reads
already committed Iter159 attempts/depths and Iter160 admitted trajectories.
It runs no new dynamics, background queries, search or continuation acquisition.
The registered ten-trajectory result and scientific source remain unchanged.

The earlier term “retained representative” needs qualification at the historical
run level. All five tested representatives were retained in at least one bound
run. However, only 12 of the 16 run bindings retained that cell winner in the final
beam. Four rank-pruned runs discarded it by width in the same iteration:
chicane_left_endpoint_rank, chicane_left_route_rank, chicane_right_endpoint_rank
and chicane_right_route_rank. A cell representative is selected before the
separate width cap; those are two distinct selection stages. The fixed protocol
remains archived with its original terminology. This notice narrows that wording;
it does not change which five pairs were tested or their observed outcomes.

For each of the 12 retained bindings, the very next issued command along the
already replayed continuation is generated and passes hard checks in the old
attempt log, then loses to another cell representative. Four of those new cell
winners also fall outside the final beam. This is a post-result localization of
repeated branch replacement, not a test of the new representative's remaining
continuation, nor proof that the replacement caused the whole search to fail.
Many of these historical runs still completed by a different path.

The extractor uses the already separately implemented Iter159 cell/ordering
replay. It binds all consumed files by SHA256 and checks that every followed
state matches its admitted continuation. It relies on retained heuristic scores;
no independent score computation is added. Five new controls distinguish cell
selection, beam-width loss, run stopping, missing children, changed states and
false hard rejection. These are post-result implementation checks, not part of
the frozen pre-acquisition qualification count.

[Machine record](proof/post-result-retention.json) ·
[Extractor](post_result_audit.py) · [Registered result](RESULT.md).
