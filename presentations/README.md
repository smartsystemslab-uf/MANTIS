# Presentations

One row per deck, newest first. Name pattern: `MANTIS_Presentation_<YYYY-MM-DD>.pptx`. Speaker notes are embedded in each slide (written for a reader, so the deck can be sent on its own); there is no separate script file.

| Date | Deck | Audience / purpose | Contents |
|---|---|---|---|
| 2026-09-24 | [MANTIS_Presentation_2026-09-24.pptx](MANTIS_Presentation_2026-09-24.pptx) | Industry meeting: the testbed end to end | 15 slides with reader-style notes: what MANTIS is, architecture, everything built so far, attack catalog, results (original + extended library), six defenses, getting started, adding your own attack, demo, scope and questions |
| Paper 1 | [../MANTIS_Demo.pptx](../MANTIS_Demo.pptx) | Paper 1 companion | Original WP0–WP8 architecture and results (frozen) |
| Paper 2 | [../MANTIS_Demo_Extensions.pptx](../MANTIS_Demo_Extensions.pptx) | Post-paper extensions | Exporters, workloads, defenses, UI |

## Rebuilding

`python presentations/_build/build_mantis_presentation.py` regenerates the deck (with its notes) from `results/`. For a new presentation, copy the builder, change `DATE`, and add a row above. Numbers are computed from the recorded results, not typed.
