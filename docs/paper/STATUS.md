# Paper status

**`ARCHIVED_NOT_SUBMISSION_READY` — this status is authoritative.**

The committed `paper.tex`, PDF, and tarball reproduce the artifact prepared on 2026-07-12. They
are retained for auditability, not as a current submission candidate. The arXiv submission was
moderation-rejected, and its source is no longer evidence-complete.

Before any peer-reviewed submission, the paper must be rewritten to include the HUGSIM transfer
null, the iteration-134 placebo result and its dose-realization confound, and bounded wording for
the decoder claim. It must state that the released implementation is benchmark-integrated rather
than production-ready, distinguish the measured NeuroNCAP gain from unresolved semantic
attribution, and route to a peer-reviewed venue before any optional arXiv appeal.

`docs/paper/build.sh` therefore permits an ordinary draft PDF build but refuses to create a
submission archive. Set `ALLOW_ARCHIVED_PAPER_BUILD=1` only to reproduce the archived package;
that flag does not make the artifact submission-ready. `BUILD_SUBMISSION_ARCHIVE=1` remains
fail-closed until both this status and the shipped-source evidence gate are current.
