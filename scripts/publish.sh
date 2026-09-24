#!/usr/bin/env bash
# Refresh the platform guide PDF and push, so the guide is rebuilt at every
# push. Commit your own changes first; this only adds the regenerated guide.
#
#   ./scripts/publish.sh            # rebuild guide, commit it if it changed, push
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build_guide.sh
git add GUIDE/MANTIS_Platform_Guide.md GUIDE/MANTIS_Platform_Guide.pdf
if ! git diff --cached --quiet; then
  git commit -m "docs: refresh platform guide"
fi
git push
