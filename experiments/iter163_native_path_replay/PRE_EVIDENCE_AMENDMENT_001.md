# Portable source binding before native acquisition

13 October 2026. Supersedes only the predicate identity encoding in source
`c77d30b595adcb9afa11ae43532a0f9baa9203f1`. No native envelope, GPU start or episode
had initialized. The plan, population, controls, geometry, replicas, outcomes,
resource bounds and stopping rules are unchanged.

Hosted CI run 38453016342 rejected the native-mask tap on the locked Python 3.11
environment: three threshold tests failed with `background_source_identity`.
Python 3.14's `FunctionDef` includes an empty `type_params` field absent from
Python 3.11. Consequently `ast.dump(..., include_attributes=False)` hashed the
same source differently. The source-identity gate worked, but its encoding was
not portable to the required runtime. This was an implementation defect, not a
driving result. The original commit and failed logs remain retained.

The corrected binding hashes the dedented UTF-8 function source, stripping only
exterior whitespace and appending one LF. Internal source bytes remain unchanged.
The complete source file remains separately hash-bound in the runtime inventory.
AST parsing now serves only the qualified instrumentation transformation, adding
the observer before the unchanged return. It does not define cross-version identity.

Local Python 3.11 accepts the corrected source binding. All 66 full-population CPU
query records and outcomes match the previously independently replayed fixture
exactly after this correction; the prior 18,250,254 scalar classifications therefore
apply to identical retained query data. These are still CPU source fixtures with
synthetic rendering. Fresh exact-source hosted CI must pass before native launch.
No test is removed, no identity check is bypassed and no scientific retry is created.
