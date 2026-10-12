"""Export an explicitly described closed result; publish only after exact-source CI.

No scientific execution or inference from the highest directory. GitHub owns channel
access; hashes bind public bytes, not scientific truth or independent review.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPOSITORY = "manfromnowhere143/sentinel"
CHANNEL = "instrument-channel"
STATUSES = {"supported", "contradicted", "replicated", "corrected", "retracted", "failed", "null", "inconclusive", "invalid"}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args])


def path_ok(path):
    return isinstance(path, str) and re.fullmatch(r"[A-Za-z0-9_./-]{1,240}", path) and ".." not in path and not path.startswith("/")


def number_at(document, field):
    require(bool(re.fullmatch(r"[a-z_]+(?:\.[a-z_]+)*", field)), "field")
    for part in field.split("."):
        document = document[part]
    require(type(document) is int and 0 <= document <= 10**12, "count_missing_or_invalid")
    return document


def export(descriptor, read, source_date):
    require(descriptor["schemaVersion"] == 1, "schema")
    commit = descriptor["evidenceCommit"]
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "commit")
    iteration = descriptor["iteration"]
    require(type(iteration) is int and iteration >= 156, "iteration")
    directory = descriptor["directory"]
    require(path_ok(directory) and directory.startswith(f"experiments/iter{iteration}_"), "directory")
    sources = []

    def blob(path):
        require(path_ok(path), "source_path")
        raw = read(path)
        require(len(raw) <= 2_000_000, "source_size")
        sources.append({"path": path, "sha256": digest(raw)})
        return raw

    state = json.loads(blob(directory + "/STATE.json"))
    admission = json.loads(blob(directory + "/proof/admission.json"))
    require(state["iteration"] == iteration and state["phase"] == "closed", "unclosed_state")
    status = state["status"]
    require(status in STATUSES and admission["status"] == status, "status_disagreement")
    for key in ["source_commit", "raw_commit"]:
        require(state[key] == admission[key] and bool(re.fullmatch(r"[0-9a-f]{40}", state[key])), "admission_identity")
    result_path = directory + "/RESULT.md"
    decision_path = directory + "/DECISION.md"
    blob(result_path)
    blob(decision_path)
    readme = blob("README.md").decode("utf-8")
    records = []
    for match in re.finditer(r"^\| \[([^\]]+)\]\((experiments/[^)]+)\) \| (.+?) \|\s*$", readme, re.M):
        label, path, summary = match.groups()
        require(path_ok(path), "record_path")
        raw = read(path)
        records.append(dict(label=label, path=path, summary=summary, sha256=digest(raw)))
    require(len(records) <= 2000 and len({r['label'] for r in records}) == len(records), "archive_inventory")
    require(any(r["path"] == result_path and r["label"] == str(iteration) for r in records), "result_not_indexed")
    require(max(int(r["label"]) for r in records if r["label"].isdigit()) == iteration, "archive_latest")
    display = {}
    for key, maximum in [("title", 90), ("summary", 350), ("boundary", 350), ("next", 280)]:
        value = descriptor[key]
        require(isinstance(value, str) and 1 <= len(value) <= maximum and "<" not in value, "display_text")
        display[key] = value
    for group, size in [("metrics", 4), ("breakdown", 3)]:
        require(len(descriptor[group]) == size, "display_population")
        display[group] = []
        for item in descriptor[group]:
            value = number_at(admission, item["field"])
            require(number_at(state, item["field"]) == value, "metric_disagreement")
            require(1 <= len(item["label"]) <= 48 and "<" not in item["label"], "metric_label")
            display[group].append(dict(label=item["label"], value=value, field=item["field"]))
    return dict(schemaVersion=1, sourceCommit=commit, generatedAt=source_date,
                iteration=iteration, status=status, resultPath=result_path, decisionPath=decision_path,
                sources=sources, records=records, **display)


def api(path, method="GET", body=None):
    args = ["gh", "api", f"repos/{REPOSITORY}/{path}", "--method", method]
    if body is not None:
        args += ["--input", "-"]
    result = subprocess.run(args, input=canonical(body) if body is not None else None, capture_output=True, check=True)
    return json.loads(result.stdout)


def ci_passed(commit):
    runs = api(f"actions/workflows/ci.yml/runs?head_sha={commit}&event=push&per_page=20")["workflow_runs"]
    runs = [r for r in runs if r["head_sha"] == commit]
    if not runs:
        return False
    latest = max(runs, key=lambda r: (r["run_number"], r["run_attempt"]))
    return latest["status"] == "completed" and latest["conclusion"] == "success"


def publish(packet):
    require(ci_passed(packet["sourceCommit"]), "evidence_ci_not_green")
    raw = canonical(packet)
    identity = digest(raw)
    pointer = dict(schemaVersion=1, sha256=identity, sourceCommit=packet["sourceCommit"], iteration=packet["iteration"])
    refs = api(f"git/matching-refs/heads/{CHANNEL}")
    refs = [r for r in refs if r["ref"] == f"refs/heads/{CHANNEL}"]
    parent = refs[0]["object"]["sha"] if refs else None
    base_tree = None
    if parent:
        previous_file = api(f"contents/latest.json?ref={parent}")
        import base64
        previous = json.loads(base64.b64decode(previous_file["content"]))
        if previous["sha256"] == identity:
            return dict(status="unchanged", channelCommit=parent, **pointer)
        require(packet["iteration"] >= previous["iteration"], "iteration_rollback")
        require(subprocess.run(["git", "merge-base", "--is-ancestor", previous["sourceCommit"], packet["sourceCommit"]], capture_output=True).returncode == 0, "source_not_descendant")
        base_tree = api(f"git/commits/{parent}")["tree"]["sha"]
    tree_body = {"tree": [dict(path="latest.json", mode="100644", type="blob", content=canonical(pointer).decode()),
                           dict(path=f"snapshots/{identity}.json", mode="100644", type="blob", content=raw.decode())]}
    if base_tree:
        tree_body["base_tree"] = base_tree
    tree = api("git/trees", "POST", tree_body)
    commit = api("git/commits", "POST", dict(message=f"Publish validated Iter{packet['iteration']} instrument evidence", tree=tree["sha"], parents=[parent] if parent else []))
    if parent:
        api(f"git/refs/heads/{CHANNEL}", "PATCH", dict(sha=commit["sha"], force=False))
    else:
        api("git/refs", "POST", dict(ref=f"refs/heads/{CHANNEL}", sha=commit["sha"]))
    served = api(f"git/ref/heads/{CHANNEL}")
    require(served["object"]["sha"] == commit["sha"], "channel_readback")
    return dict(status="published", channelCommit=commit["sha"], **pointer)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    require(git("remote", "get-url", "origin").decode().strip().removesuffix(".git") == f"https://github.com/{REPOSITORY}", "repository")
    descriptor = json.loads(git("show", "HEAD:instrument/progress.json"))
    commit = git("rev-parse", "HEAD").decode().strip()
    descriptor["evidenceCommit"] = commit
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "commit")
    require(subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], capture_output=True).returncode == 0, "source_ancestry")
    packet = export(descriptor, lambda path: git("show", f"{commit}:{path}"), git("show", "-s", "--format=%cI", commit).decode().strip())
    args.output.write_bytes(canonical(packet))
    if args.publish:
        print(json.dumps(publish(packet), sort_keys=True))
    else:
        print(json.dumps(dict(iteration=packet["iteration"], records=len(packet["records"]), sha256=digest(canonical(packet)))))


if __name__ == "__main__":
    main()
