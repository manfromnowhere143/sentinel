# Decision-relevant primary-source check, 14 October 2026

OMPL's [directed sampler documentation](https://ompl.kavrakilab.org/classompl_1_1control_1_1SimpleDirectedControlSampler.html)
describes choosing among sampled controls by distance to a target and returning a
control duration. Its [control space information documentation](https://ompl.kavrakilab.org/classompl_1_1control_1_1SpaceInformation.html)
separates propagation step size, duration and propagation while valid. These are
living documentation pages, retrieved on this date, not version-pinned release
claims. The inspected 2.0.1 implementations remain retained in
[Iter166's upstream inventory](../iter166_independent_planner/UPSTREAM.json).

The methodological implication is ours: test the directed connector independently
and account for every intermediate propagation before changing the tree algorithm.
The proposed two-step receding connector is Sentinel code, not OMPL's released
sampler, and this study invokes no OMPL solve. It does not test a claim about OMPL's
relative performance. Longer durations, alternative metrics and tree integration
remain separate decisions. Recentness or implementation complexity supplies no
evidence of superiority; this narrow controlled comparison can change the next
implementation decision without another broad literature survey.
