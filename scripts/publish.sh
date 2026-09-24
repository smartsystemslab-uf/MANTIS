#!/usr/bin/env bash
# Refresh generated PDFs and push, so a PDF never lags its source.
# Commit your own changes first; this only adds regenerated PDFs.
#
#   ./scripts/publish.sh            # rebuild PDFs, commit them if changed, push
#
# Rebuilt: the platform guide (always, it stamps the date and commit) and Paper 2's
# PDF (when its .tex is newer). Paper 1 (paper/mantis_paper.*) is frozen and never touched here.
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build_guide.sh
if [ paper/mantis_paper2.tex -nt paper/mantis_paper2.pdf ]; then
  (cd paper && tectonic mantis_paper2.tex >/dev/null 2>&1) && echo "Built paper/mantis_paper2.pdf"
fi
git add GUIDE/MANTIS_Platform_Guide.md GUIDE/MANTIS_Platform_Guide.pdf \
        paper/mantis_paper2.tex paper/mantis_paper2.pdf
if ! git diff --cached --quiet; then
  git commit -m "docs: refresh generated PDFs"
fi
git push
