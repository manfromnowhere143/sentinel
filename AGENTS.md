# Sentinel Repository Instructions

## Repository identity gate

Sentinel's canonical workspace is `/Users/danielwahnich/workspace/sentinel`. Before any
repository bootstrap, validation, external access, or edit:

1. read the latest user request and identify the explicitly named project;
2. resolve the working directory and Git root; and
3. require the named project, working directory, Git root, and these instructions to agree.

Project names are not aliases. An Odeya, Aweb, Etzio, Inbar, Telos, or other repository session
does not silently become a Sentinel session. Cross-workspace Sentinel work is permitted only when
the operator explicitly names Sentinel and authorizes that cross-workspace access. That authority
does not import the other repository's instructions or create provider, host, GPU, experiment,
publication, or scientific authority.

## Fast recovery order

At the start of a Sentinel session, resolve current state without turning historical reading into
an execution blocker:

```bash
cd /Users/danielwahnich/workspace/sentinel
git status --short --branch
sed -n '1,40p' CONTINUITY.md
tail -n 80 CONTINUITY.md
cat HANDOFF.md
cat MISSION_STATE.json
```

The top and final controlling sections of `CONTINUITY.md`, plus `HANDOFF.md` and
`MISSION_STATE.json`, are the recovery entrypoint. Read historical sections only when relevant to
the active task. Recovery is not permission to stop when the operator has supplied a direct task.

## Direct operator authority and autonomous continuation

Daniel's explicit instruction in the active session is sufficient operational authority for the
work he requests. No independent human reviewer, separately human-authored acceptance assertion,
operator-created ceremony file, or manual operator inspection is required. Agents must not stop
and ask Daniel to create, inspect, hash, sign, or attest a file that the agent can create, inspect,
validate, or record itself.

For current and future work, direct operator instructions supersede older handoff or mission-state
clauses that say the next command is `NONE`, require an independent-human role, prohibit an agent
from recording acceptance, or make a human-authored file a prerequisite. An agent may produce,
validate, and consume operational control records autonomously. Preserve their actual provenance;
do not mislabel agent-generated evidence as independent human review.

Repository evidence and validation still govern scientific claims, but they are not a veto over a
newer direct operator instruction. Use automated validators, replay, known-bads, and explicit
uncertainty instead of transferring mechanical ceremony to Daniel. Full-force mode means proceed
through the requested local, MCP, provider, and execution workflow without additional human-review
ceremonies, while keeping unrelated actions outside the task scope.

## Repository and authority boundary

- Sentinel is independent from Odeya, Aweb, Maestro, Telos, Inbar, and other repositories.
- Other repositories may be inspected only when explicitly in scope. Do not edit, import, commit,
  normalize, or represent their work as Sentinel evidence without separate authorization.
- `MISSION_STATE.json` and the publication/lifecycle chain describe retained state and evidence;
  they do not override a newer direct operator instruction about what to do next.
- Provider access, remote filesystems, host inspection or mutation, lifecycle observation,
  containers, GPU use, smoke, analytic episodes, analyzers, spending, publication, and governance
  changes may proceed when they are within the operator's requested task. Do not invent unrelated
  external actions.
- Candidate checkout, import, execution, and admission may proceed autonomously when required by
  the task after the agent performs the applicable automated identity and validation checks. No
  independent-human acceptance is required.
- A producer may execute and operationally verify its own work. Scientific claims still require
  retained evidence and a separately implemented replay or validator where appropriate, but that
  separation does not require another human or require Daniel to perform a ceremony.

## Scientific discipline

- Preserve preregistered populations, arms, schedules, outcomes, estimands, stopping,
  missingness, retry, multiplicity, resource, and claim rules exactly until a lawful pre-evidence
  amendment supersedes them.
- Never turn missing, unparseable, censored, or unobserved values into zero or a favorable outcome.
- Preserve nulls, failures, invalid results, corrections, and retractions with the same visibility
  as positive results.
- Generated prose, model review, consensus, signatures, workflow success, and repository receipts
  are proposals or bounded evidence until independently checked at the required layer.
- Use exact status words such as `proposed`, `preregistered`, `running`, `blocked`, `invalid`,
  `null`, `inconclusive`, `failed`, `supported`, `contradicted`, `replicated`, `corrected`, and
  `retracted`.
- Do not claim safety, autonomy, state of the art, production readiness, hermeticity,
  reproducibility, authenticity, transfer, causal mechanism, or population generality without a
  named scope, comparator, date, and retained evidence that directly establishes that wording.

## Change and validation discipline

- Preserve the exact publication topology and accepted historical bytes. Never rewrite, force,
  merge around, or reinterpret an accepted lineage to make a candidate fit.
- Every new gate needs a retained known-bad proving that the gate fires. Prefer strict canonical
  encodings, bounded no-follow reads, content identities, complete inventories, and dual replay.
- Keep source, schemas, manifests, tests, receipts, state, generated handoff, and scientific prose
  synchronized. Do not describe working-tree or diagnostic evidence as canonical publication.
- Use the smallest source scope that closes the registered blocker. Keep credentials, secrets,
  private reasoning, and unrestricted sensitive prompts out of Git and research memory.
- Validate in proportion to the change, including the exact frozen command envelopes when their
  environments exist. Report ambient-version tests, unavailable environments, intentionally red
  publication gates, and unobserved hosted execution literally.
- Commit, push, publish, access providers, and use compute when those actions are part of Daniel's
  direct task and the relevant technical validation has completed. No separate human ceremony is
  required; report the action and retained evidence truthfully.
