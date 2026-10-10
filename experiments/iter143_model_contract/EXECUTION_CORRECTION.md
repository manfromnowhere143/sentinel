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
