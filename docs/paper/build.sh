#!/bin/bash
# Build the paper from source, and rebuild the submission tarball FROM THE SAME SOURCE.
#
# Why this script exists: on 2026-07-14 the arXiv submission was rejected, and the audit found
# that iter124's manuscript freshness gate had validated docs/paper/MANUSCRIPT.md -- a file that
# was never submitted -- while the submitted paper.tex omitted the campaign's own HUGSIM transfer
# boundary. The general defect is drift between the source and the artifact that actually ships.
# The paper is the one artifact in this repository that did not regenerate from committed
# evidence; it existed because someone once clicked compile. It does now.
#
# This script makes source -> pdf -> tarball a single reproducible act, and prints the SHA256 of
# every shipped artifact so drift is visible instead of silent.
#
# Requires TeX Live (BasicTeX is sufficient: brew install --cask basictex).
# Usage: bash docs/paper/build.sh
set -euo pipefail

export PATH="/Library/TeX/texbin:$PATH"
cd "$(dirname "$0")"

# Determinism: pdflatex stamps a creation date into the PDF and tar embeds mtimes, so an
# unchanged source would otherwise produce different bytes on every build -- the paper would be
# the one artifact in this repository that cannot reproduce. Pin the clock to the last commit
# that touched paper.tex, so identical source => identical bytes, and a changed PDF always means
# a changed source.
SOURCE_DATE_EPOCH="$(git log -1 --format=%ct -- paper.tex 2>/dev/null || echo 1)"
export SOURCE_DATE_EPOCH
export FORCE_SOURCE_DATE=1

command -v pdflatex >/dev/null || {
  echo "FAIL: pdflatex not found. Install with: brew install --cask basictex"
  echo "      then: eval \"\$(/usr/libexec/path_helper)\""
  exit 1
}

echo "== pdflatex =="
pdflatex --version | head -1

echo "== pass 1/2 =="
pdflatex -interaction=nonstopmode -halt-on-error paper.tex > /tmp/paper_build_1.log 2>&1 || {
  echo "FAIL: pass 1. Errors:"; grep -E "^! " /tmp/paper_build_1.log | head -5; exit 1; }
echo "== pass 2/2 (resolves references) =="
pdflatex -interaction=nonstopmode -halt-on-error paper.tex > /tmp/paper_build_2.log 2>&1 || {
  echo "FAIL: pass 2. Errors:"; grep -E "^! " /tmp/paper_build_2.log | head -5; exit 1; }

grep -E "Output written" /tmp/paper_build_2.log

# undefined references are a silent-drift class: fail loudly
if grep -qiE "undefined (citation|reference)" /tmp/paper_build_2.log; then
  echo "FAIL: undefined citations/references:"
  grep -iE "undefined (citation|reference)" /tmp/paper_build_2.log | head -5
  exit 1
fi

# the tarball must be rebuilt from the SAME source, never hand-assembled
echo "== rebuilding submission tarball from this source =="
rm -f sentinel-arxiv-submission.tar.gz
# built deterministically (pinned mtime/uid/gid, no gzip timestamp) so identical source always
# yields an identical tarball; bsdtar on macOS cannot pin mtime, so do it in python
python3 - "$SOURCE_DATE_EPOCH" <<'PY'
import gzip, io, sys, tarfile
epoch = int(sys.argv[1])
members = ["./paper.tex", "./figures/fig1_benchmark.pdf",
           "./figures/fig2_leadtime.pdf", "./figures/fig3_routing.pdf"]
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
    for name in members:
        info = tar.gettarinfo(name)
        info.mtime, info.uid, info.gid, info.uname, info.gname = epoch, 0, 0, "", ""
        with open(name, "rb") as fh:
            tar.addfile(info, fh)
with open("sentinel-arxiv-submission.tar.gz", "wb") as out:
    # mtime=0 keeps the gzip header timestamp out of the bytes
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as gz:
        gz.write(buf.getvalue())
PY
tar tzf sentinel-arxiv-submission.tar.gz

echo "== shipped artifact SHA256 (drift is visible here) =="
shasum -a 256 paper.tex paper.pdf sentinel-arxiv-submission.tar.gz

# the tarball's paper.tex must be byte-identical to the source paper.tex
tmp=$(mktemp -d); tar xzf sentinel-arxiv-submission.tar.gz -C "$tmp"
if ! cmp -s paper.tex "$tmp/paper.tex"; then
  echo "FAIL: tarball paper.tex differs from source paper.tex"; rm -rf "$tmp"; exit 1
fi
rm -rf "$tmp"
echo "OK: tarball paper.tex is byte-identical to source paper.tex"
echo "BUILD_OK"
