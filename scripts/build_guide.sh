#!/usr/bin/env bash
# Rebuild GUIDE/MANTIS_Platform_Guide.pdf from GUIDE/MANTIS_Platform_Guide.md.
# The markdown is the source of truth; the PDF is generated. The date and the
# commit the guide was built on top of are stamped in automatically.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v pandoc >/dev/null   || { echo "pandoc is required (brew install pandoc)"; exit 1; }
command -v tectonic >/dev/null || { echo "tectonic is required (brew install tectonic)"; exit 1; }
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
DATE="$(date +"%B %d, %Y")"
TMP="$(mktemp -t mantis_guide.XXXXXX).md"
sed -e "s/@@DATE@@/${DATE}/" -e "s/@@COMMIT@@/${COMMIT}/" GUIDE/MANTIS_Platform_Guide.md > "$TMP"
pandoc "$TMP" -o GUIDE/MANTIS_Platform_Guide.pdf --pdf-engine=tectonic
rm -f "$TMP"
echo "Built GUIDE/MANTIS_Platform_Guide.pdf (${DATE}, on top of ${COMMIT})"
