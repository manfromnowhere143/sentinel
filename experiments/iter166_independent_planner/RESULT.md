# Iter166: independent planner qualification is invalid

The independent checker rejects the first reported completion:
`missing_completion_checkpoint`. OMPL reaches the route goal at 4.5 seconds in
bend-left, before the final required checkpoint at 8 seconds. The adapter used
route completion alone as its terminal condition. Its preregistered admission
required both checkpoints. This is an adapter contract defect, not an admitted
completion or evidence that the checkpoint should be removed.

The producer records four runs: bend-left and chicane-right report completion at
4.5 and 6.5 seconds; bend-right and chicane-left exhaust 18,000 attempts. The checker
stops on the first invalid completion. **No four-case admission or source-comparison
qualification is claimed.** Raw records remain intact, including approximate paths.
No source RRT search or native episode ran. The four workers and supervisor are reaped.

Source `1a183fd214c8accab129f0c358feaa4c4c1244d1`; raw committed first at
`1bc7cfc6e5696d7e667c84a0d6519af5ad707d34`. The checker command, failure and process
receipt are retained in `proof`. The preinitialization abbreviated-hash rejection
is also retained separately; it acquired no scientific outcome.
