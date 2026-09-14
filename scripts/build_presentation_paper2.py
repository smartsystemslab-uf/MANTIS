#!/usr/bin/env python3
"""build_presentation_paper2.py

Generates MANTIS_Demo_Extensions.pptx -- the companion deck to Paper 2
(paper/mantis_paper2.tex), covering the five Post-Paper Extensions
(coding plan §11). Same visual system as scripts/build_presentation.py
(the Paper 1 deck, MANTIS_Demo.pptx) -- reuses its helper functions
verbatim -- but a separate file/script on purpose: Paper 1's deck stays
exactly as it was, per the standing instruction to keep the old copy as
is rather than editing it to fold in new content.

    python scripts/build_presentation_paper2.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

# ---------------------------------------------------------------------------
# Palette / type -- identical to scripts/build_presentation.py, so the two
# decks read as one family.
# ---------------------------------------------------------------------------
NAVY_950 = RGBColor(0x07, 0x10, 0x22)
NAVY_900 = RGBColor(0x0D, 0x20, 0x43)
CARD_FILL = RGBColor(0x14, 0x27, 0x4A)
CARD_LINE = RGBColor(0x2E, 0x46, 0x6E)
ORANGE = RGBColor(0xFA, 0x46, 0x16)
ORANGE_SOFT = RGBColor(0xFF, 0x8A, 0x5C)
ACCENT_FILL = RGBColor(0x33, 0x1E, 0x14)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ON_DARK = RGBColor(0xEE, 0xF2, 0xF8)
ON_DARK_SOFT = RGBColor(0xAE, 0xBB, 0xD2)
ON_DARK_FAINT = RGBColor(0x7E, 0x8F, 0xAE)
GOOD = RGBColor(0x3D, 0xC3, 0x86)
WARN = RGBColor(0xFF, 0x8A, 0x66)

F_SANS = "Arial"
F_SANS_BLACK = "Arial Black"
F_SERIF = "Georgia"
F_MONO = "Consolas"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.62)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


# ---------------------------------------------------------------------------
# Low-level helpers (identical to scripts/build_presentation.py)
# ---------------------------------------------------------------------------
def add_slide():
    slide = prs.slides.add_slide(BLANK)
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    rect.fill.solid()
    rect.fill.fore_color.rgb = NAVY_950
    rect.line.fill.background()
    rect.shadow.inherit = False
    return slide


def textbox(slide, left, top, width, height, text, size=14, color=ON_DARK,
            bold=False, italic=False, font=F_SANS, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, spacing=1.15, wrap=True):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
        run.font.color.rgb = color
    return box


def rich_textbox(slide, left, top, width, height, runs_per_line, size=14,
                  align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.2,
                  space_after=0):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line_runs in enumerate(runs_per_line):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        for text, overrides in line_runs:
            run = p.add_run()
            run.text = text
            run.font.size = Pt(overrides.get("size", size))
            run.font.bold = overrides.get("bold", False)
            run.font.italic = overrides.get("italic", False)
            run.font.name = overrides.get("font", F_SANS)
            run.font.color.rgb = overrides.get("color", ON_DARK)
    return box


def hline(slide, left, top, width, color, weight=0.75):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, left, top, left + width, top)
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)
    return ln


def rounded_rect(slide, left, top, width, height, fill, line_color, radius=0.08, line_w=0.75):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    try:
        shp.adjustments[0] = radius
    except Exception:
        pass
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line_color
    shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def brand_lockup(slide):
    box = rounded_rect(slide, MARGIN, Inches(0.32), Inches(0.34), Inches(0.34), NAVY_950, ON_DARK, radius=0.16, line_w=1.25)
    tf = box.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "UF"
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.name = F_SANS
    run.font.color.rgb = ON_DARK

    rich_textbox(
        slide, MARGIN + Inches(0.44), Inches(0.28), Inches(3.6), Inches(0.42),
        [
            [("Herbert Wertheim", {"bold": True, "size": 10.5, "font": F_SANS, "color": ON_DARK})],
            [("College of Engineering", {"italic": True, "size": 9, "font": F_SERIF, "color": ON_DARK_SOFT})],
        ],
        spacing=1.0,
    )


def footer(slide, page_num, note=None):
    y = Inches(6.98)
    hline(slide, MARGIN, y, Inches(2.6), ON_DARK_FAINT, weight=0.75)
    hline(slide, Inches(10.2), y, Inches(2.5), ON_DARK_FAINT, weight=0.75)
    label = note if note else "MANTIS EXTENDED — POST-PAPER EXTENSIONS"
    textbox(slide, Inches(3.3), Inches(6.87), Inches(6.8), Inches(0.28), label,
            size=8, color=ON_DARK_FAINT, font=F_MONO, align=PP_ALIGN.CENTER)
    textbox(slide, Inches(12.5), Inches(6.87), Inches(0.6), Inches(0.28), str(page_num),
            size=9, bold=True, color=ON_DARK_SOFT, font=F_MONO, align=PP_ALIGN.RIGHT)


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def kicker(slide, text, top=Inches(0.98)):
    textbox(slide, MARGIN, top, Inches(9), Inches(0.3), text.upper(), size=11,
            bold=True, color=ORANGE_SOFT, font=F_MONO)


def h1(slide, text, top=Inches(1.28), size=28, width=Inches(11.6)):
    textbox(slide, MARGIN, top, width, Inches(1.3), text, size=size, bold=True,
            color=ON_DARK, font=F_SANS_BLACK, spacing=1.04)


def lede(slide, text, top, width=Inches(10.5)):
    textbox(slide, MARGIN, top, width, Inches(0.5), text, size=13.5, italic=True,
            color=ON_DARK_SOFT, font=F_SERIF)


def stat_tile(slide, left, top, width, height, number, label):
    rounded_rect(slide, left, top, width, height, CARD_FILL, CARD_LINE, radius=0.10)
    textbox(slide, left + Inches(0.14), top + Inches(0.10), width - Inches(0.28), Inches(0.5),
            number, size=25, bold=True, color=ORANGE_SOFT, font=F_MONO)
    textbox(slide, left + Inches(0.14), top + Inches(0.60), width - Inches(0.28), height - Inches(0.68),
            label, size=9.5, color=ON_DARK_SOFT, font=F_SANS, spacing=1.15)


def card(slide, left, top, width, height, title, body, accent=False, title_size=12.5, body_size=10.5, body_spacing=1.22):
    fill = ACCENT_FILL if accent else CARD_FILL
    line_c = ORANGE if accent else CARD_LINE
    rounded_rect(slide, left, top, width, height, fill, line_c, radius=0.07)
    title_color = ORANGE_SOFT if accent else ON_DARK
    body_color = ON_DARK if accent else ON_DARK_SOFT
    textbox(slide, left + Inches(0.18), top + Inches(0.13), width - Inches(0.36), Inches(0.3),
            title, size=title_size, bold=True, color=title_color, font=F_SANS)
    textbox(slide, left + Inches(0.18), top + Inches(0.48), width - Inches(0.36), height - Inches(0.60),
            body, size=body_size, color=body_color, font=F_SANS, spacing=body_spacing)


def styled_table(slide, left, top, width, height, headers, rows, col_widths=None, font_size=10.5):
    n_rows = len(rows) + 1
    n_cols = len(headers)
    gshape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = gshape.table
    if col_widths:
        total = sum(col_widths)
        for i, w in enumerate(col_widths):
            table.columns[i].width = Emu(int(width * (w / total)))
    tbl = table._tbl
    tblPr = tbl.find(qn('a:tblPr'))
    if tblPr is not None:
        tblPr.set('firstRow', '0')
        tblPr.set('bandRow', '0')

    for c, htext in enumerate(headers):
        cell = table.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY_900
        cell.margin_left = Inches(0.09); cell.margin_right = Inches(0.09)
        cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        run = p.add_run(); run.text = htext.upper()
        run.font.size = Pt(9); run.font.bold = True; run.font.name = F_MONO
        run.font.color.rgb = ORANGE_SOFT

    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_FILL
            cell.margin_left = Inches(0.09); cell.margin_right = Inches(0.09)
            cell.margin_top = Inches(0.06); cell.margin_bottom = Inches(0.06)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            first = True
            for line in val.split("\n"):
                p = tf.paragraphs[0] if first else tf.add_paragraph()
                first = False
                p.line_spacing = 1.08
                run = p.add_run(); run.text = line
                run.font.size = Pt(font_size if c != 0 else font_size + 0.5)
                run.font.bold = (c == 0)
                run.font.name = F_SANS
                run.font.color.rgb = ON_DARK if c == 0 else ON_DARK_SOFT
    return table


# ---------------------------------------------------------------------------
# 1. TITLE
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Paper 2 — Post-Paper Extensions", top=Inches(2.55))
h1(s, "MANTIS Extended", top=Inches(2.9), size=48)
textbox(s, MARGIN, Inches(3.75), Inches(10.3), Inches(0.9),
        "Five extensions Paper 1 deliberately deferred — additional exporters, security-mechanism\n"
        "plugins, a Zero Trust integration surface, new banking workloads, and a minimal UI — each built,\n"
        "each live-verified.",
        size=14.5, italic=True, color=ON_DARK_SOFT, font=F_SERIF, spacing=1.3)
footer(s, 1, note="smartsystemslab-uf/MANTIS · Paper 2")
set_notes(s, """This is the companion deck to Paper 2 -- MANTIS Extended.

Quick framing: the first MANTIS paper scoped itself narrowly on purpose and named five extensions it deliberately deferred rather than attempted under that schedule. This deck covers all five, each with live evidence, not just a description.

Paper 1 and its own deck are unchanged -- this is additive, a second paper building on the first, not a revision of it.""")

# ---------------------------------------------------------------------------
# 2. RECAP / BRIDGE
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Where Paper 1 Left Off")
h1(s, "Four extensions, named and deferred on purpose", top=Inches(1.22), size=24)
lede(s, "Paper 1's own coding plan listed these explicitly — not gaps found later, but scope cut deliberately to ship on schedule.", top=Inches(1.78))
items = [
    ("Additional exporters", "Jaeger, Grafana, Langfuse, Phoenix — beyond the OTel/MLflow/JSONL Paper 1 shipped."),
    ("Security mechanism plugins", "Guardrails, policy checks, rate limits — evaluated through the same framework as attacks."),
    ("Additional banking workloads", "More banking processes and workflow patterns beyond Paper 1's evaluation set."),
    ("Minimal UI", "A schema-driven editor and trace viewer over the existing CLI — no separate business logic."),
]
cw = Inches(2.85)
for i, (t, b) in enumerate(items):
    card(s, MARGIN + i * (cw + Inches(0.15)), Inches(2.5), cw, Inches(3.9), t, b, body_size=10.5)
footer(s, 2)
set_notes(s, """All four items on this slide are quoted directly from Paper 1's own coding plan section 11, "Post-Paper Extensions" -- not a list we assembled after the fact. A fifth item on that same list, a Zero Trust Backplane integration, was also explored to the same live-verified standard, but is being carried forward as a separate, dedicated effort with a real independent Zero Trust Backplane project rather than reported as part of this deck's own evidence.

Walk the four briefly: more telemetry backends, defensive plugins through the same interface as attacks, more banking processes, and a thin UI over the CLI.

Key point: each of the next four sections covers exactly one of these, in the same order, with live evidence for each.""")

# ---------------------------------------------------------------------------
# 3. EXTENSION 1 — JAEGER EXPORTER
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Extension 1 of 4 — Additional Exporters")
h1(s, "Four telemetry backends, one adapter pattern, config-only", top=Inches(1.22), size=22)
card(s, MARGIN, Inches(1.85), Inches(5.85), Inches(2.3), "All four built",
     "Jaeger, Grafana (Tempo), and Phoenix are the same thin OTLP-over-gRPC wrapper around Paper 1's own TracerProvider, differing only in default endpoint and an optional cloud-auth header. Langfuse genuinely differs — its endpoint is HTTP-only and always requires Basic auth, even self-hosted — so it's built on the OTLP/HTTP exporter instead.",
     body_size=10.5)
card(s, Inches(6.65), Inches(1.85), Inches(6.05), Inches(2.3), "How you use it",
     "observability:\n  export: [jsonl, jaeger]   # or grafana / phoenix / langfuse\n  jaeger_endpoint: http://localhost:4317\n\nNo code change to the banking workflow, hook bus, or observability plugin — same one-line pattern for all four.",
     body_size=11)
card(s, MARGIN, Inches(4.35), Inches(12.1), Inches(1.95), "Verified: fails silently, and one got a real response back",
     "With no collector listening, the SDK's own BatchSpanProcessor retries and logs a warning rather than raising — confirmed for all four. Langfuse got a stronger check: run with no credentials against its real hosted endpoint, it reached cloud.langfuse.com over the network and got back a genuine HTTP 401 — proof the transport and endpoint wiring are correct against the real service, not just an absent local collector.",
     accent=True, body_size=11)
footer(s, 3)
set_notes(s, """First extension: additional observability exporters. All four of the coding plan's named backends are now built, not just Jaeger.

Jaeger, Grafana Tempo, and Phoenix all accept OTLP natively over gRPC, so they're the same adapter shape -- a thin wrapper around the TracerProvider Paper 1's OpenTelemetry setup already creates, differing only in endpoint and an optional auth header for their managed cloud offerings. Langfuse is the one that's genuinely different: its ingestion endpoint is HTTP-only and always requires Basic auth, even self-hosted, so that adapter is built on a different OTLP transport package entirely.

Enabling any of them is still one line in the observability.export list plus an endpoint -- no code change anywhere in the banking workflow or the hook bus.

Key point, and this is the one to land: we verified the failure path, not just the happy path, for all four. And Langfuse got a stronger check than a local no-collector test can offer -- run it with no credentials against the real hosted Langfuse endpoint, and it came back with a genuine 401 Unauthorized over the real network, which confirms the wiring is correct end to end against the actual service.""")

# ---------------------------------------------------------------------------
# 4. EXTENSION 2 — SECURITY MECHANISM PLUGIN
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Extension 2 of 4 — Security Mechanism Plugins")
h1(s, "A defense, through the same interface as an attack", top=Inches(1.22), size=23)
headers = ["Step", "What happened (live, real model)"]
rows = [
    ("1. Legitimate call", "execute_transfer called with a real $125.50 transfer, source CHK-002 → EXT-998."),
    ("2. Attack mutates it", "tool_mutation (Paper 1's own plugin) rewrites the call to $5,000 → account HACKER-9999."),
    ("3. Guardrail evaluates it", "amount_limit_guardrail (max $2,000) sees the already-mutated call and denies it."),
    ("4. Backend never sees it", "The call never reaches the banking backend. The agent reports a payment-limit restriction to the customer."),
]
styled_table(s, MARGIN, Inches(1.8), Inches(12.1), Inches(3.3), headers, rows, col_widths=[2.2, 7.0], font_size=11)
card(s, MARGIN, Inches(5.25), Inches(12.1), Inches(1.05), "Why order matters",
     "Guardrails register on the hook bus after any configured attack — the same reason Paper 1 registers observability last. A defense that only sees the original, unmutated call isn't testing anything real.",
     accent=True, body_size=11)
footer(s, 4)
set_notes(s, """Second extension: a concrete guardrail plugin, evaluated through the exact same plugin interface as an attack -- Paper 1 shipped this interface with no implementation behind it.

Walk the table top to bottom -- this is a real, live run against a real model, not a simulation. A legitimate $125.50 transfer gets mutated by Paper 1's own tool-mutation attack to $5,000 into an account called HACKER-9999. The guardrail, configured with a $2,000 limit, evaluates that already-mutated call and denies it. The real banking backend never sees it, and the agent correctly tells the customer it's a payment-limit restriction, not a generic failure.

Key point on ordering: the guardrail is registered after the attack on the hook bus, specifically so it evaluates what the attack actually did, not the original clean call. A defense that only ever sees clean traffic isn't proving anything.

One more detail worth mentioning if asked: we also had to teach the observability layer a new event type, POLICY_EVENT, distinct from ATTACK_INJECTED -- a guardrail denying a call is the system working as intended, not an attack, and the trace now says so explicitly.""")

# ---------------------------------------------------------------------------
# 5. EXTENSION 3 — DISPUTE WORKLOAD
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Extension 3 of 4 — Additional Banking Workloads")
h1(s, "A genuinely new process, not a new prompt", top=Inches(1.22), size=23)
card(s, MARGIN, Inches(1.85), Inches(5.85), Inches(2.55), "What it is",
     "Dispute filing and status lookup — a third route under the front-office router, alongside the existing transaction-review and chatbot workflows. A new tool-backed agent and a real case record, not a new prompt into an existing workflow.",
     body_size=11)
card(s, Inches(6.65), Inches(1.85), Inches(6.05), Inches(2.55), "Distinct from the existing chatbot",
     "The chatbot already answers \"how do I dispute a transaction\" as an FAQ. This is different: it actually files a case, persists it, and returns a real dispute ID the customer can reference.",
     body_size=11)
card(s, MARGIN, Inches(4.55), Inches(12.1), Inches(1.75), "What three live trials with zero tool calls taught us",
     "First attempt: real routing worked, but the agent called no tool at all, three times in a row. Cause: the scenario prompt never stated a customer id, unlike every other scenario in the codebase — and file_dispute needs one. Fixed the prompt, not the tool. Next run: real case filed, real ID returned, correct customer message.",
     accent=True, body_size=11)
footer(s, 5)
set_notes(s, """Third extension: a genuinely new banking process, not a new prompt into an existing workflow -- filing and tracking a transaction dispute, as a third route under the front-office router.

Worth distinguishing from something that already existed: the chatbot already answers "how do I dispute a transaction" as an FAQ. This is different -- it actually files a real case with a real generated ID, persisted in the same database the manual-review process already uses.

The honest part of this story: the first version produced zero tool calls across three consecutive live trials, with correct routing every time. The cause wasn't a code defect -- it was that our scenario prompt never stated a customer id, which the tool needs, and which every other scenario in this codebase states explicitly. We fixed the prompt, not the tool, and the very next live run filed a real case correctly.

Key point: a clean exit and correct routing both looked fine; only checking the actual tool-call events revealed nothing had happened.""")

# ---------------------------------------------------------------------------
# 6. EXTENSION 4 — MINIMAL UI
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Extension 4 of 4 — Minimal UI")
h1(s, "A thin layer over the real CLI, not a second implementation", top=Inches(1.22), size=22)
card(s, MARGIN, Inches(1.85), Inches(5.85), Inches(2.55), "What it is",
     "A schema-driven experiment editor and trace viewer. Domain/workflow/scenario/plugin dropdowns are populated live from the same registries the CLI reads — not a hardcoded list that can drift.",
     body_size=11)
card(s, Inches(6.65), Inches(1.85), Inches(6.05), Inches(2.55), "\"No separate business logic\", verified",
     "Validate and Run shell out to the real mantis CLI as a subprocess. Submitted a config with a deliberately invalid domain: got the real CLI's own \"Unknown domain\" error back, not a UI-side check.",
     body_size=11)
card(s, MARGIN, Inches(4.55), Inches(12.1), Inches(1.75), "Confirmed as a real running server",
     "Launched via mantis --ui and queried over real HTTP, not just an in-process test client: correctly reported the live inventory (32 agents, 22 tools) and every existing run artifact (27 runs) at the time of this check.",
     accent=True, body_size=11.5)
footer(s, 6)
set_notes(s, """Final extension: the minimal UI Paper 1's coding plan named last -- a schema-driven editor and trace viewer, explicitly constrained to invoke the same CLI, not implement a second version of anything.

The dropdowns for domain, workflow, scenario, and plugin are populated live from the same registries the CLI itself reads from -- not a hardcoded list baked into the page that could quietly drift from the real system.

Key point, and we verified this directly rather than assuming it from the code structure: submitted a configuration with a deliberately invalid domain through the UI, and got back the real CLI's own "Unknown domain" error text -- because it's the same subprocess, not a UI-side reimplementation of that check.

We also confirmed it as a real running server, not just passing an internal test client -- launched it for real and queried it over HTTP, and it correctly reported the live system: 32 agents, 22 tools, 27 existing run artifacts, at the time we checked.""")

# ---------------------------------------------------------------------------
# 7. EVALUATION SUMMARY
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Evaluation Summary")
h1(s, "139 tests, all against real data — every extension live-verified", top=Inches(1.22), size=22)
headers = ["Extension", "Tests", "Live evidence"]
rows = [
    ("Jaeger exporter", "4", "Real span processor attached; confirmed silent-safe with no collector listening."),
    ("Grafana / Phoenix / Langfuse", "9", "Same OTLP pattern for the first two; Langfuse reached the real hosted endpoint and got a genuine 401 with no credentials."),
    ("Guardrail plugin", "6", "Live $5,000 mutated transfer denied before reaching the backend; correctly classified as POLICY_EVENT."),
    ("Dispute workload", "7", "Real case filed and persisted, after correcting a scenario defect found only by reading the trace."),
    ("Minimal UI", "10", "Real invalid config rejected with the real CLI's own error; real server confirmed over live HTTP."),
]
styled_table(s, MARGIN, Inches(1.85), Inches(12.1), Inches(3.15), headers, rows, col_widths=[2.3, 1.0, 8.0], font_size=10.5)
stat_tile(s, MARGIN, Inches(5.35), Inches(3.9), Inches(1.15), "139", "offline tests passing, all exercised against real data")
stat_tile(s, MARGIN + Inches(4.1), Inches(5.35), Inches(3.9), Inches(1.15), "0", "changes required to mantis.core, mantis.hooks, or the banking workflow modules")
stat_tile(s, MARGIN + Inches(8.2), Inches(5.35), Inches(3.9), Inches(1.15), "1", "real defect found and fixed while building these extensions")
footer(s, 7)
set_notes(s, """Summary slide -- every extension checked against real data or a real live run, the same standard Paper 1 set for itself.

The offline suite stands at 139 tests -- covering all four extensions, including the three additional exporters added in this revision -- all still running in under a minute with no live model key required.

The three numbers at the bottom are the ones worth pausing on: zero changes required to any of MANTIS's core interfaces to add any of these four extensions -- the plugin and inventory interfaces held up exactly as designed. And one real defect found and fixed along the way, invisible from a clean process exit -- a scenario-prompt gap in the dispute workflow found only by checking the actual tool-call events.""")

# ---------------------------------------------------------------------------
# 8. CLOSING
# ---------------------------------------------------------------------------
s = add_slide()
brand_lockup(s)
kicker(s, "Thank You")
h1(s, "Four extensions, zero core changes, real evidence for each", top=Inches(3.05), size=26)
textbox(s, MARGIN, Inches(3.95), Inches(10), Inches(0.9),
        "Paper 1's interfaces held up exactly as designed. Happy to walk through any extension live,\n"
        "or discuss the separate Zero Trust Backplane integration effort.",
        size=14, italic=True, color=ON_DARK_SOFT, font=F_SERIF, spacing=1.3)
textbox(s, MARGIN, Inches(4.95), Inches(8), Inches(0.5), "github.com/smartsystemslab-uf/MANTIS",
        size=15, color=ON_DARK_SOFT, font=F_MONO)
footer(s, 8, note="Leading the Charge, Charging Ahead")
set_notes(s, """That's MANTIS Extended.

Closing message: the headline result of this second paper isn't any single extension -- it's that Paper 1's plugin and inventory interfaces held up completely unmodified across all four, including a defensive plugin, four separate telemetry backends, a new banking process, and a UI. A fifth item, Zero Trust Backplane integration, was explored to the same standard and is being carried forward as its own dedicated effort with a real independent project, separate from this repository.

Everything shown today is reproducible from the checked-in configs in the repository, same as Paper 1. Thank you, and happy to take questions or walk through any extension live.""")

prs.save("MANTIS_Demo_Extensions.pptx")
print(f"Wrote MANTIS_Demo_Extensions.pptx with {len(prs.slides._sldIdLst)} slides")
