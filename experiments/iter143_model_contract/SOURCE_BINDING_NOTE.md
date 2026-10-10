# Source dependency binding

Before implementation or fixture execution, add the retained controller utils.py
source to INPUTS. The extracted dynamics method calls its principal_value helper.
Binding and extracting that exact function avoids substituting a local approximation.
The helper matches the closed parent commit. Fixture definitions, tolerances,
population, verdicts and resource limits are unchanged.
