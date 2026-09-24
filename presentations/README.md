# Presentations

One row per deck, newest first. Name pattern: `MANTIS_Presentation_<YYYY-MM-DD>.pptx`, with a read-aloud script (`_Script.md`/`.pdf`) beside it. Speaker notes are also embedded in each slide.

| Date | Deck | Audience / purpose | Contents |
|---|---|---|---|
| 2026-09-24 | [MANTIS_Presentation_2026-09-24.pptx](MANTIS_Presentation_2026-09-24.pptx) · [script](MANTIS_Presentation_2026-09-24_Script.pdf) | Industry meeting: the testbed end to end | 15 slides, about 8 minutes of speech plus a live demo (shortened for a tight slot): what MANTIS is, architecture, everything built so far, attack catalog, results (original + extended library), six defenses, getting started, adding your own attack, demo, scope and questions |
| Paper 1 | [../MANTIS_Demo.pptx](../MANTIS_Demo.pptx) | Paper 1 companion | Original WP0–WP8 architecture and results (frozen) |
| Paper 2 | [../MANTIS_Demo_Extensions.pptx](../MANTIS_Demo_Extensions.pptx) | Post-paper extensions | Exporters, workloads, defenses, UI |

## Rebuilding

`python presentations/_build/build_mantis_presentation.py` regenerates the deck and script from `results/`. For a new presentation, copy the builder, change `DATE`, and add a row above. Numbers are computed from the recorded results, not typed.
