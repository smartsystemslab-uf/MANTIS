"""Builds presentations/MANTIS_Presentation_2026-10-30.pptx (speaker notes
embedded, written for a reader) -- a short deck covering what's new since the
2026-09-24 deck: the Zero Trust Backplane toggle, the minimal UI, and the
AML office toggle.

Visual format matches the UF Herbert Wertheim College of Engineering
reference deck exactly (30min_with_Demo.pdf), not the earlier MANTIS house
style: UF Blue / UF Orange, dark-navy "primary" boxes, light-blue-tint
"secondary" boxes, orange-tint "active/highlighted" boxes, a bold navy
takeaway line above a thin rule, and the small-caps college footer with a
page number on every content slide.

Known limitation: the real UF wordmark/crest and the title-slide building
photo are not available here, so the title slide uses a solid UF Blue field
with a text-based "UF" mark in the same position/style instead of the real
logo image -- swap in the real asset file if/when available.

    python presentations/_build/build_update_2026-10-30.py

Requires python-pptx and Pillow.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck_kit import *  # noqa
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

REPO = Path(__file__).resolve().parents[2]
DATE = "2026-10-30"
OUT_DIR = REPO / "presentations"
NAME = f"MANTIS_Presentation_{DATE}"
IMAGES = REPO / "paper" / "figures"
TESTS_OFFLINE, TESTS_BOTH = "853", "880"

# ---------------------------------------------------------------- UF palette
# Official University of Florida brand colors (UF Blue / UF Orange), plus the
# supporting neutrals the reference deck actually uses. Strict per request --
# no MANTIS-house teal/amber in this deck.
UF_FONT = "Calibri"
UF_BLUE = "0021A5"        # UF Blue -- titles, takeaway lines, accents
UF_ORANGE = "FA4616"      # UF Orange -- section eyebrows, title-slide accents
DARK_NAVY = "0B1F3A"      # primary diagram boxes (dark, white text)
LIGHT_TINT = "EAF0F8"     # secondary diagram boxes (light, dark text)
ORANGE_BG = "FDEEE4"      # highlighted/active box fill
ORANGE_LINE = UF_ORANGE
GREEN_BG, GREEN_TXT = "E3F5EA", "1C7C4C"   # ALLOW
RED_BG, RED_TXT = "FBEAEC", "A32638"       # DENY / REJECT
FOOTER_GRAY = "6B7A8F"
RULE_GRAY = "CBD6E2"
INK2 = "1A2B3C"

SCRIPT = []
d = Deck()
_page = {"n": 0}


def slide(bg=WHITE, title_text="", notes="", minutes=1.0):
    SCRIPT.append((title_text, notes, minutes))
    s = d.slide(bg=bg, notes=notes)
    _page["n"] += 1
    s._page_no = _page["n"]
    return s


def uf_title(s, txt):
    text(s, 0.55, 0.35, 11.8, 0.65, txt, size=27, bold=True, color=UF_BLUE, font=UF_FONT)


def uf_footer(s):
    """College footer + thin rule + page number, exactly like the reference."""
    rect(s, 0.55, 6.98, 12.23, 0.012, fill=RULE_GRAY)
    text(s, 0.55, 7.08, 9.5, 0.3,
         "U N I V E R S I T Y   O F   F L O R I D A   H E R B E R T   W E R T H E I M   C O L L E G E   O F   E N G I N E E R I N G",
         size=8.5, color=FOOTER_GRAY, font=UF_FONT)
    text(s, 11.9, 7.08, 0.9, 0.3, str(s._page_no), size=9, color=FOOTER_GRAY, font=UF_FONT, align="r")


def uf_takeaway(s, txt):
    text(s, 0.55, 6.52, 12.2, 0.4, txt, size=14.5, bold=True, color=UF_BLUE, font=UF_FONT)


def uf_card(slide_, x, y, w, h, kind="secondary"):
    """kind: primary (dark navy, white text) | secondary (light tint) | active (orange tint)."""
    if kind == "primary":
        return rect(slide_, x, y, w, h, fill=DARK_NAVY, line=None)
    if kind == "active":
        return rect(slide_, x, y, w, h, fill=ORANGE_BG, line=ORANGE_LINE, line_w=1.25)
    return rect(slide_, x, y, w, h, fill=LIGHT_TINT, line=None)


def uf_box_label(slide_, x, y, w, h, label, kind="secondary", size=14):
    color = WHITE if kind == "primary" else (UF_ORANGE if kind == "active" else INK2)
    uf_card(slide_, x, y, w, h, kind)
    text(slide_, x + 0.08, y, w - 0.16, h, label, size=size, bold=True, color=color,
         font=UF_FONT, align="c", anchor="m")


def uf_arrow_h(slide_, x, y, w=0.3, h=0.22):
    arrow(slide_, x, y, w, h, fill=UF_BLUE)


def eyebrow(slide_, x, y, w, txt, color=UF_ORANGE):
    text(slide_, x, y, w, 0.3, txt.upper(), size=11.5, bold=True, color=color, font=UF_FONT)


# =============================================================== 1. Title
s = slide(UF_BLUE, "MANTIS -- This Week", (
    "Quick update, not a full re-introduction: three things landed since the last deck. "
    "A real, toggleable integration of the independent Zero Trust Backplane project. "
    "A minimal browser UI over the same CLI. "
    "And new this week: a toggleable AML office, ported from the legacy codebase MANTIS's banking agents were originally extracted from. "
    "Everything is off by default and verified live, not just unit-tested."), 0.5)
rect(s, 0.0, 0.0, 13.333, 7.5, fill=UF_BLUE)
# Text-based college mark (placeholder for the real UF wordmark/crest asset).
rect(s, 0.55, 0.45, 0.62, 0.62, fill=WHITE)
text(s, 0.55, 0.47, 0.62, 0.58, "UF", size=22, bold=True, color=UF_BLUE, font=UF_FONT, align="c", anchor="m")
text(s, 1.3, 0.42, 4.6, 0.3, "Herbert Wertheim", size=12, bold=True, color=WHITE, font=UF_FONT)
text(s, 1.3, 0.68, 4.6, 0.3, "College of Engineering", size=12, bold=True, color=WHITE, font=UF_FONT)
text(s, 1.3, 0.96, 4.6, 0.26, "UNIVERSITY of FLORIDA", size=10, color=WHITE, font=UF_FONT)
text(s, 0.8, 2.3, 11.0, 1.7, "MANTIS -- This Week", size=56, bold=True, color=WHITE, font=UF_FONT)
text(s, 0.8, 3.75, 10.5, 1.0, "Zero Trust  ·  the UI  ·  the AML Office", size=26, bold=True, color=UF_ORANGE, font=UF_FONT)
text(s, 0.8, 5.5, 9.5, 0.4, "October 30, 2026", size=15, bold=True, color=UF_ORANGE, font=UF_FONT)
text(s, 0.8, 5.9, 9.5, 0.4, "Smart Systems Lab · Research testbed, synthetic data only", size=14, color=UF_ORANGE, font=UF_FONT)
rect(s, 0.8, 6.95, 2.2, 0.012, fill=WHITE)
text(s, 3.1, 6.82, 7.1, 0.3, "L E A D I N G   T H E   C H A R G E ,   C H A R G I N G   A H E A D", size=10.5, color=WHITE, font=UF_FONT, align="c")
rect(s, 10.35, 6.95, 2.2, 0.012, fill=WHITE)

# =============================================================== 2. MANTIS in brief
s = slide(WHITE, "MANTIS in brief", (
    "One-slide refresher. MANTIS is a configuration-driven security testbed built on a real, unmodified banking multi-agent system. "
    "Five fixed control points -- input, agent, interaction, tool, output -- let an attack, failure, or defense plugin declare itself entirely in YAML. "
    "Front, mid, and back office are always on: 34 agents, 27 tools. "
    "Everything we're covering today -- Zero Trust, the AML office -- is a toggle on top of that unchanged core."), 0.75)
uf_title(s, "MANTIS in brief")
eyebrow(s, 0.55, 1.1, 8, "THE TESTBED")
cols = [("A real system under test", "Unmodified banking multi-agent system. Front / mid / back office: 34 agents, 27 tools, a real backend.", "secondary"),
        ("Five control points, one hook bus", "Input, agent, interaction, tool, output. An attack, failure, or defense is a plugin declared in YAML.", "primary"),
        ("Evidence, not exit codes", "Every run writes a manifest, a trace, and a scorecard -- verified against the real trace, every time.", "secondary")]
for i, (h, t, kind) in enumerate(cols):
    x = 0.55 + i * 4.13
    uf_card(s, x, 1.55, 3.9, 2.7, kind)
    tcol = WHITE if kind == "primary" else INK2
    hcol = WHITE if kind == "primary" else UF_BLUE
    text(s, x + 0.25, 1.75, 3.4, 0.7, h, size=15.5, bold=True, color=hcol, font=UF_FONT)
    text(s, x + 0.25, 2.5, 3.4, 1.6, t, size=13, color=tcol, font=UF_FONT)
eyebrow(s, 0.55, 4.55, 8, "WHAT'S NEW")
uf_card(s, 0.55, 4.9, 12.23, 1.4, "active")
text(s, 0.85, 5.1, 11.6, 1.0, [
    {"runs": [("Two new toggles, zero risk to the rest. ", {"bold": True, "color": UF_ORANGE}),
              ("Zero Trust and the AML office are both off by default -- every existing config's behavior is byte-identical whether or not they exist.", {"color": INK2})]}],
     size=15, font=UF_FONT)
uf_takeaway(s, "Everything below is a toggle on top of that unchanged core.")
uf_footer(s)

# =============================================================== 3. Zero Trust Backplane
s = slide(WHITE, "Zero Trust Backplane (toggleable)", (
    "A real integration of the independent Citi_P3_Zero_Trust_Backplane project's signed Policy Decision Point -- not a reimplementation. "
    "A stock install never imports it; it's an optional dependency, guarded by a try/except so it's genuinely unregistered rather than registered-but-broken when absent. "
    "Toggle it with a dedicated zero_trust block in any config, or the same checkbox in the UI. "
    "The policy itself is generated from MANTIS's own live inventory: an agent may act on a tool in its own domain, everything else is denied by the PDP's own default. "
    "Live-verified: same-domain allow, cross-domain deny, an unrecognized agent denied before a challenge is even issued, and two full legitimate runs through the real PDP completing identically to the undefended baseline. "
    "Eleven regression tests guard it against future drift."), 1.1)
uf_title(s, "Zero Trust Backplane: real PDP, toggled per run")
eyebrow(s, 0.55, 1.1, 6, "POLICY DECISION")
uf_box_label(s, 0.55, 1.5, 2.6, 0.75, "Agent request", "secondary", size=13.5)
uf_arrow_h(s, 3.25, 1.75)
uf_box_label(s, 3.65, 1.5, 2.9, 0.75, "PDP policy check", "active", size=13.5)
uf_arrow_h(s, 6.65, 1.75)
rect(s, 7.05, 1.15, 2.55, 0.6, fill=GREEN_BG)
text(s, 7.05, 1.15, 2.55, 0.6, "ALLOW — same domain", size=12.5, bold=True, color=GREEN_TXT, font=UF_FONT, align="c", anchor="m")
rect(s, 7.05, 1.95, 2.55, 0.6, fill=RED_BG)
text(s, 7.05, 1.95, 2.55, 0.6, "DENY — everything else", size=12.5, bold=True, color=RED_TXT, font=UF_FONT, align="c", anchor="m")
text(s, 9.85, 1.5, 2.9, 0.75, "Unknown identity or\nunrecognized call: deny\nbefore a challenge issues.", size=11.5, color=FOOTER_GRAY, font=UF_FONT)
rect(s, 0.55, 2.85, 12.23, 0.012, fill=RULE_GRAY)
eyebrow(s, 0.55, 3.05, 6, "WHAT IT IS")
text(s, 0.55, 3.4, 5.9, 2.1, [
    {"runs": [("Real external project. ", {"bold": True, "color": UF_BLUE}),
              ("The independent Citi_P3_Zero_Trust_Backplane's own signed PDP -- not reimplemented here.", {"color": INK2})], "space_after": 9},
    {"runs": [("Fails closed. ", {"bold": True, "color": UF_BLUE}),
              ("Unreachable PDP, or anything but ALLOW, means deny -- not a silent pass-through.", {"color": INK2})], "space_after": 9},
    {"runs": [("Opt-in dependency. ", {"bold": True, "color": UF_BLUE}),
              ("Guarded import -- a stock install never touches it.", {"color": INK2})]}], size=13.5, font=UF_FONT)
eyebrow(s, 6.78, 3.05, 6, "LIVE-VERIFIED")
for i, t in enumerate(["Same-domain allow, cross-domain deny", "Unrecognized agent denied pre-challenge",
                        "Shared tool name resolves correctly, both directions", "2 full legitimate runs identical to the undefended baseline"]):
    y = 3.4 + i * 0.5
    badge(s, 6.78, y + 0.02, 0.32, str(i + 1), fill=UF_BLUE, size=11)
    text(s, 7.25, y, 5.5, 0.45, t, size=13, color=INK2, font=UF_FONT, anchor="m")
uf_takeaway(s, "zero_trust: {enabled: true}  --  11 regression tests guard it against drift.")
uf_footer(s)

# =============================================================== 4. Minimal UI
s = slide(WHITE, "The minimal UI", (
    "A schema-driven experiment editor and trace viewer over the same mantis CLI -- no separate business logic. "
    "Validate and Run shell out to the exact same subprocess a terminal user would invoke. "
    "Domain, workflow, scenario, and plugin dropdowns are populated live from the running registries, not hardcoded, so they can never drift from the real system. "
    "Verified directly: a deliberately invalid config submitted through the UI comes back with the real CLI's own error text, not a UI-side check. "
    "Dedicated toggle fieldsets for Zero Trust and, new this week, the AML office sit right next to the generic attack and policy dropdowns -- this is a real screenshot of it running against a real AML office run, not a mockup."), 1.0)
uf_title(s, "The minimal UI: a thin layer over the real CLI")
img_path = IMAGES / "ui_editor_zt_crop.png"
rect(s, 0.5, 1.25, 4.6, 5.15, fill=LIGHT_TINT)
if img_path.exists():
    s.shapes.add_picture(str(img_path), Inches(0.62), Inches(1.37), height=Inches(4.95))
eyebrow(s, 5.4, 1.25, 7, "NO SEPARATE BUSINESS LOGIC")
uf_card(s, 5.4, 1.6, 7.35, 2.5, "secondary")
text(s, 5.65, 1.8, 6.9, 2.1, [
    {"text": "Validate / Run → the real mantis CLI subprocess.", "space_after": 9},
    {"text": "Schema, registries, inventory → the same live objects mantis --inventory reads.", "space_after": 9},
    {"text": "Trace / evaluation / hook-coverage → the same JSON files every other consumer reads.", "space_after": 9},
    {"text": "Campaign → two real CLI invocations chained, not UI-side aggregation."}], size=13.5, color=INK2, font=UF_FONT)
eyebrow(s, 5.4, 4.3, 7, "TURN IT ON")
uf_card(s, 5.4, 4.65, 7.35, 1.6, "primary")
text(s, 5.65, 4.85, 6.9, 0.4, "mantis --ui", size=16, bold=True, color=UF_ORANGE, font="Courier New")
text(s, 5.65, 5.3, 6.9, 0.3, "http://127.0.0.1:8765", size=13, color=WHITE, font="Courier New")
text(s, 5.65, 5.7, 6.9, 0.4, "Dedicated toggle fieldsets: Zero Trust + AML Office", size=12.5, color="BFD0E8", font=UF_FONT)
uf_takeaway(s, "A real screenshot of the real UI -- not a mockup.")
uf_footer(s)

# =============================================================== 5. AML Office
s = slide(WHITE, "The AML office (toggleable, new this week)", (
    "MANTIS's banking agents were extracted from a larger legacy codebase, Citi_P3. That legacy codebase had a working AML investigation office "
    "-- an investigator agent, a SAR drafting agent, four real detection functions -- that never made the transition when the rest was translated into MANTIS. "
    "This week we ported it. Four detection functions are unchanged from the source: structuring detection is a real sliding-window cumulative-deposit analysis, "
    "threshold-anomaly flags anything over five times a customer's baseline, mule-ring detection is real closed-loop graph traversal over a customer's transaction history, "
    "and identity verification is Levenshtein name scoring weighted thirty-thirty-forty against date of birth and ID number. "
    "Plus a real alert lifecycle: open, in-investigation, cleared or escalated to SAR. "
    "It's a fourth banking domain, off by default, toggled exactly like Zero Trust."), 1.1)
uf_title(s, "AML office: four real detectors, ported from Citi_P3")
eyebrow(s, 0.55, 1.1, 10, "PORTED, NOT REINVENTED")
dets = [("Structuring detection", "Sliding-window cumulative deposits; default $10,000 / 7 days", "primary"),
        ("Threshold anomaly", "Flags a transaction over 5x a customer's baseline peak", "secondary"),
        ("Mule-ring detection", "Closed-loop graph traversal over a customer's own transaction history", "secondary"),
        ("Identity verification", "Levenshtein name + DOB + ID number, weighted 0.30 / 0.30 / 0.40", "primary")]
for i, (h, t, kind) in enumerate(dets):
    x = 0.55 + (i % 2) * 6.14
    y = 1.5 + (i // 2) * 1.65
    uf_card(s, x, y, 5.9, 1.45, kind)
    tcol = WHITE if kind == "primary" else INK2
    hcol = UF_ORANGE if kind == "primary" else UF_BLUE
    badge(s, x + 0.2, y + 0.2, 0.42, str(i + 1), fill=UF_ORANGE if kind == "primary" else UF_BLUE, size=13)
    text(s, x + 0.78, y + 0.17, 4.9, 0.45, h, size=14.5, bold=True, color=hcol, font=UF_FONT)
    text(s, x + 0.78, y + 0.65, 4.9, 0.7, t, size=12, color=tcol, font=UF_FONT)
rect(s, 0.55, 5.0, 12.23, 0.012, fill=RULE_GRAY)
eyebrow(s, 0.55, 5.18, 6, "TURN IT ON")
text(s, 0.55, 5.55, 5.6, 0.75, "aml_office:\n  enabled: true", size=14, font="Courier New", color=UF_BLUE)
text(s, 6.6, 5.4, 5.9, 0.85, "Off by default — every existing config's root agent is byte-identical to before this domain existed.", size=12.5, color=FOOTER_GRAY, font=UF_FONT)
uf_takeaway(s, "Four real detectors, one toggle -- the identical discipline as Zero Trust.")
uf_footer(s)

# =============================================================== 6. Live verification found 2 bugs
s = slide(WHITE, "Live verification found 2 real bugs", (
    "The whole point of verifying against the real trace, not a clean exit code: live verification against five new AML scenarios found two real integration defects "
    "before we could honestly call the extension complete. First, a routing gap -- the identity-verification scenario was misrouted to the front office instead of the AML office, "
    "because the root agent's own routing instruction never mentioned identity verification by name. Second, an unreachable capability -- the alert-triage tool existed, "
    "was correctly implemented, was unit-tested directly as a function -- but no agent in the actual built tree had it on its toolset at all, so it could never be called live. "
    "Neither was caught by the unit test suite, because both are properties of the live agent tree, not of any single ported function in isolation. "
    "Both fixed and re-verified live, including one effect confirmed by reading the real database state back afterward, not just trusting the model's own report. "
    "All five scenarios now score 1.0 on tool-use correctness and workflow outcome, every time."), 1.25)
uf_title(s, "Live verification found 2 real bugs")
eyebrow(s, 0.55, 1.1, 10, "...BEFORE WE CALLED THE AML OFFICE “DONE”")
for i, (bug, desc, fix) in enumerate([
    ("BUG 1 — Routing gap", "Identity verification was misrouted to the front office -- the root agent's instruction never named it as an AML task.",
     "Wording, not logic: both the root agent's and the AML router's instructions now name identity verification and alert triage explicitly."),
    ("BUG 2 — Unreachable capability", "Alert-triage was implemented and unit-tested, but no agent in the built tree had it on its toolset.",
     "Wired the three alert-lifecycle tools onto the investigator agent. Re-verified: a real database status transition, confirmed by reading it back.")]):
    x = 0.55 + i * 6.17
    uf_card(s, x, 1.5, 5.95, 4.85, "active")
    text(s, x + 0.25, 1.68, 5.45, 0.5, bug, size=16, bold=True, color=UF_ORANGE, font=UF_FONT)
    rect(s, x + 0.25, 2.25, 5.45, 0.012, fill=ORANGE_LINE)
    eyebrow(s, x + 0.25, 2.42, 5, "WHAT HAPPENED", color=UF_BLUE)
    text(s, x + 0.25, 2.78, 5.45, 1.35, desc, size=13.5, color=INK2, font=UF_FONT)
    eyebrow(s, x + 0.25, 4.2, 5, "FIX", color=UF_BLUE)
    text(s, x + 0.25, 4.56, 5.45, 1.6, fix, size=13.5, color=INK2, font=UF_FONT)
uf_takeaway(s, "Neither bug was caught by the unit suite -- both are properties of the live agent tree.")
uf_footer(s)

# =============================================================== 7. Where things stand
s = slide(WHITE, "Where things stand", (
    "Both toggles follow the identical discipline: opt-in, off by default, byte-identical existing behavior when absent, live-verified rather than just unit-tested. "
    f"The full offline test suite stands at {TESTS_OFFLINE} passing with neither optional dependency installed, {TESTS_BOTH} with both Zero Trust and AML installed, zero failures either way. "
    "Every capability here -- Zero Trust, the AML office, the UI -- is reproducible from a committed configuration file against the real backend and a real model, not a one-off claim."), 0.9)
uf_title(s, "Where things stand")
eyebrow(s, 0.55, 1.1, 10, "BY THE NUMBERS")
for i, (n, l) in enumerate([(TESTS_OFFLINE, "tests passing offline"), (TESTS_BOTH, "with both toggles' deps installed"),
                             ("0", "failures, either way"), ("2", "new toggles, zero impact when off")]):
    x = 0.55 + i * 3.08
    text(s, x, 1.55, 2.85, 0.9, n, size=42, bold=True, color=UF_BLUE, font=UF_FONT)
    text(s, x, 2.4, 2.85, 0.7, l, size=12.5, color=FOOTER_GRAY, font=UF_FONT)
rect(s, 0.55, 3.25, 12.23, 0.012, fill=RULE_GRAY)
eyebrow(s, 0.55, 3.45, 10, "THE SAME DISCIPLINE, BOTH TIMES")
for i, t in enumerate(["Opt-in, off by default", "Byte-identical existing behavior when disabled",
                        "Real external logic, not reimplemented or invented", "Verified against the live trace / database, not a clean exit code"]):
    x = 0.55 + (i % 2) * 6.13
    y = 3.85 + (i // 2) * 1.15
    uf_card(s, x, y, 5.85, 0.95, "secondary" if i % 2 == 0 else "active")
    hcol = UF_BLUE if i % 2 == 0 else UF_ORANGE
    badge(s, x + 0.2, y + 0.26, 0.4, str(i + 1), fill=hcol, size=13)
    text(s, x + 0.75, y, 4.9, 0.95, t, size=13.5, color=INK2, font=UF_FONT, anchor="m")
uf_takeaway(s, "Reproducible from a committed config, against the real backend and a real model.")
uf_footer(s)

# =============================================================== 8. Discussion
s = slide(WHITE, "Discussion", (
    "That's the update: a real Zero Trust Backplane integration, a minimal UI over the same CLI, and this week's AML office, ported faithfully from Citi_P3 and "
    "live-verified hard enough to find and fix two real bugs before calling it done. Code, both papers, and the platform guide are all in the repository."), 0.5)
uf_title(s, "Discussion")
text(s, 0.8, 2.6, 11.5, 1.6, "What should we verify live next?", size=34, bold=True, color=UF_BLUE, font=UF_FONT, align="c")
text(s, 0.8, 4.2, 11.5, 0.4, "Zero Trust  ·  the UI  ·  the AML Office — all toggleable, all live-verified", size=15, color=FOOTER_GRAY, font=UF_FONT, align="c")
text(s, 0.8, 5.0, 11.5, 0.4, "Code, papers, and platform guide: the repository. Synthetic data only.", size=13, color=FOOTER_GRAY, font=UF_FONT, align="c")
uf_footer(s)

# ---------------------------------------------------------------- save deck
OUT_DIR.mkdir(exist_ok=True)
d.save(OUT_DIR / f"{NAME}.pptx")
print(f"saved {NAME}.pptx ({d.n} slides), notes embedded in the deck")
print("\n".join(WARNINGS) if WARNINGS else "no text-fit warnings")
