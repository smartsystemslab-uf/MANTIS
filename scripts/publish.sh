#!/usr/bin/env bash
# Refresh generated PDFs and push, so a PDF never lags its source.
# Commit your own changes first; this only adds regenerated PDFs.
#
#   ./scripts/publish.sh            # rebuild PDFs, commit them if changed, push
#
# Rebuilt: the platform guide (always, it stamps the date and commit), Paper 2's
# PDF (when its .tex is newer), and each presentation script PDF (when its .md
# is newer). Paper 1 (paper/mantis_paper.*) is frozen and never touched here.
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build_guide.sh
if [ paper/mantis_paper2.tex -nt paper/mantis_paper2.pdf ]; then
  (cd paper && tectonic mantis_paper2.tex >/dev/null 2>&1) && echo "Built paper/mantis_paper2.pdf"
fi
for md in presentations/*_Script.md; do
  [ -e "$md" ] || continue
  pdf="${md%.md}.pdf"
  if [ "$md" -nt "$pdf" ]; then
    pandoc "$md" -o "$pdf" --pdf-engine=tectonic -V geometry:margin=1in -V fontsize=12pt >/dev/null 2>&1 && echo "Built $pdf"
  fi
done
git add GUIDE/MANTIS_Platform_Guide.md GUIDE/MANTIS_Platform_Guide.pdf \
        paper/mantis_paper2.tex paper/mantis_paper2.pdf presentations/*_Script.md presentations/*_Script.pdf
if ! git diff --cached --quiet; then
  git commit -m "docs: refresh generated PDFs"
fi
git push
