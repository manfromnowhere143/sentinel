# Engineering review — 11 October 2026

The retained HUGSIM source and exact asset hashes govern this experiment. The
[official implementation](https://github.com/hyzhou404/HUGSIM) documents scene restoration and
simulation; current upstream code is context, not a replacement for the retained runtime.
[PyTorch v2.3.1 numerical-accuracy notes](https://raw.githubusercontent.com/pytorch/pytorch/v2.3.1/docs/source/notes/numerical_accuracy.rst)
explain that mathematically equivalent CPU/GPU operations need not be bitwise identical and
that TF32 changes precision. We therefore retain the observed runtime settings, compare complete
masks, and distinguish exact agreement from a declared numerical sensitivity band. The band
is not a certified floating-point error bound. No GPU/software-version universality follows.

The actual source constructs its canonical box in binary64, then casts transformed vertices
to binary32 for collision. Local qualification exposed a fixture that compared those two
representations prematurely; the corrected fixture compares the source collision inputs.
Failure output remains retained. Source-method fixtures use NumPy CPU operations in place of
torch; synthetic integration fixtures use explicit synthetic points and ground poses. They are
not restored-scene or CUDA outcomes. Separate scalar geometry imports no producer or simulator.

The experiment answers a measurement question with two fixed historical frame witnesses and
no new driving episodes. Complete pre-selection attributes, filter membership, selected order,
source masks and counts make silent favorable pruning detectable. Four replica/frame records
bind two unique poses. Source-bound checkpoint decoding is not an independently reproduced
model loader or a physical reconstruction validation. Occupancy, drivable road boundaries,
useful recovery, information value and competitive superiority require further evidence.

Reuse the qualified provider identity/ownership transport, denied-start classifier and watchdog.
A capacity refusal may permit the one registered retry only after no-start reconciliation and
120 seconds after the first attempt closes. An initialized extraction cannot be retried. Raw
chunks are canonical evidence; the redundant transport archive remains locally retained and
hash-bound but is excluded from Git. Preserve all previous results, master and root WIP.
