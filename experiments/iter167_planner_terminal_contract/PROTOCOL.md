# Terminal-clock correction, otherwise unchanged Iter166 protocol

Apply the complete Iter166 protocol and exact runtime identities. Before accepting
an edge with route progress >=1, require its frame to be at least the largest
checkpoint time divided by0.25. No fractional checkpoint frame is admissible.
The edge counts against attempts whether accepted or rejected; rejected premature
completion does not perform a background query. Goal and scalar admission retain
the same both-checkpoint requirement. No old source or raw artifact is edited.

The newly retained known-bad reproduces a clear early-terminal edge under Iter166
and rejects it under Iter167. A terminal edge at the final checkpoint remains
eligible. The original source clock maps7.75/9.0 seconds toframes31/36.
All new source is frozen before the four seeded runs; commit raw before admission.
Resources and stopping are unchanged from Iter166. This is a correction study on
exposed fixtures, with no native or source-scene claim.
