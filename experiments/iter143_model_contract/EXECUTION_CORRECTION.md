# Local fixture execution correction

The first complete source probe exited 1 in the synthetic low-speed adapter: one
terminal row was indexed by a zero-length mask. No complete raw fixture artifact
was written. This invocation is invalid, and its traceback is retained. Fix the
adapter to produce one candidate and reject it with a one-element false mask;
the actual upstream resampling code and registered fixture values remain unchanged.
Add a test of the complete adapter at N10/tf1 and retain unexpected exceptions as
invalid records. Re-execute the local diagnostic after committing the tested repair.

The independent inventory command wrote its artifact and reported returncode0.
Its outer wrapper then failed because command metadata reused case_inventory.json.
The inventory and child stdout/stderr survive unchanged; wrapper timing was not
retained and remains null. Move subsequent command receipts into proof/commands,
reject an output/receipt collision before invocation, and do not rerun the inventory.

These are implementation failures in the new diagnostic harness. They change no
source model, fixture population, tolerance, input binding, endpoint or cloud scope.
The protocol already requires retained initial failures and explicit corrections.

## Second invalid invocation

The repaired sampler reached actor dispatch, where the synthetic state had float64
storage but the original planner writes next_xyrv.float() by indexed assignment.
Torch rejected that mismatch. raw_fixtures_v2.json is explicitly invalid; no complete
measurement record exists. Commit b2184ae2dcd3af19aee4096a743e6d629eb7e5bf has an
imprecise subject saying completed measurements; its retained artifact is invalid,
and that subject must not be used as evidence of completion.

Use float32 actor-state storage matching the original planner's ordinary float-list
construction, and add a three-step test of the actual dispatch adapter. Ego dynamics
fixtures remain float64; upstream source and all thresholds remain unchanged. Retain
both failed invocations and run the repaired diagnostic under a new output name.
