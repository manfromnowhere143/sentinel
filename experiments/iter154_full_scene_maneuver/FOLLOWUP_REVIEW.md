# Adjacent baseline review — 11 October 2026

After the protocol freeze, reviewed Sections III–V and Table III of
[ECO v1, 25 September 2026](https://arxiv.org/html/2609.31383v1). It fixes executed history and the
predicted endpoint while reshaping intermediate waypoints; its interface uses plans and ego
history. Table III reports aggregate gains while some policies have worse no-collision components.
Its HUGSIM test uses 185 scenes and three seeds. These are author-reported results, not reproduced
Sentinel comparisons. Code compatibility and a full baseline reproduction remain unassessed.

Inference for Sentinel: control competence must be separated from added-information value,
and collision/progress components must remain visible alongside any aggregate score. ECO is
a future baseline candidate, not a replacement for the missing background-geometry measurement
identified by Iter154. No claim of novelty or competitive superiority follows from this review.
