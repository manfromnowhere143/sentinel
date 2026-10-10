# Iter145 asset closure correction and resumed inspection

2026-10-10. Daniel explicitly resumed the mission after the retained stopping point.
The prior VM start and inspection envelope remain closed. The prior failed inventory
is retained unchanged. No experiment outcome or controller threshold is being changed.

Correct two local inventory defects before a new measurement: validate a present,
well-formed empty scenario plan list; and resolve only the historical Iter46 actor
alias `<car>/postprocess/shadow.pth -> ..`. Retain logical path, physical path, exact
link text and metadata. Read canonical regular files with no-follow checks; require
SHA-256 and size from the Iter45 asset manifest. Reject other links, path escapes,
missing/malformed lists and changed content. Preserve scenario bytes and actor identities.
Map closure must reflect the actual UnifiedMap loader, NuScenes metadata and trajdata
cache dependencies; a directory-exists assertion does not establish closure.

A second bounded inspection is permitted after source tests and commit: one start
request of the same VM ID 3834622546652649531 in sunlit-unison-487018-b0/us-west1-a,
g2-standard-8 with one L4. At most 1,800 seconds from request to shutdown, conservative
incremental compute bound $3/hour and cap $1.50. Recheck the published price before
start. Existing persistent disk baseline is excluded; this is not an invoice.
No new disk, snapshot or bucket, no package install and zero live simulator/model episodes.
Use a new exclusive control directory. Inspect resources, actual alias targets,
metadata/cache inventories and installed loader source. Return at most 100 MiB of
inventory/source; remote output at most 1 GiB. Local free >=15 GiB, host free >=100 GiB.
An occupied host aborts without stopping unrelated jobs. Retain a local watchdog and
host timer, clock-skew observations, final owned stop and TERMINATED readback.

Allow at most three SSH readiness probes during initial boot, spaced at least 10 seconds;
these are transport probes, not capacity or episode retries. Inspect only the named
host. No GPU smoke is permitted by this binding. A separate source-bound, finite smoke
binding must precede GPU execution after asset/resource checks are satisfied.

## Inspection-driven correction before remeasurement

A recount of the first retained report corrects the stopping-point description:
its 28 unavailable entries were 20 actor files (ten distinct actor IDs) and eight
legitimately empty frozen runtime source files, not 28 actor files. The resumed
inspection observed all 20 actor files at their exact release identities; the eight
empty files still failed the positive-size check. Admit an empty runtime source only
when its expected frozen digest is SHA-256 of empty bytes. Missing files stay missing;
empty model, map or scenario assets remain rejected. Preserve the original report.

Installed UnifiedDataset source shows construction considers the entire nusc_trainval
cache, even when UnifiedMap later selects one scene. Bind complete regular-file trees
under /root/.unified_data_cache, /datasets/nuscenes-full/v1.0-trainval and
/datasets/nuscenes-full/maps, with explicit required tables, both target scene caches
at dt 0.10/0.50, and all four vector maps/search indexes. Bound inventory to 100,000
files per tree, 16 GiB per file and 600 seconds. This is read-only identity inventory,
not loader or route-execution qualification. Retain installed source evidence.

The initial broad cache listing exceeded its 5,000-entry diagnostic cap and was
retained as failed. A selected-path diagnostic then established the necessary scope.
Two initial SSH commands encountered port-22 boot readiness failure; the third succeeded.
No additional VM start, simulator/model execution or package installation occurred.
