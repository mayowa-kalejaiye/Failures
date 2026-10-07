"""Defence slides for the Failures final-year project. 16:9, 11 slides.

Design system: deep-navy + gold on white; kicker labels; stat cards for
results; gold-run bullets; footers with slide numbers; speaker notes.
"""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
OUT = ROOT / "FAILURES_Defence_Slides.pptx"

NAVY = RGBColor(0x1B, 0x3A, 0x5C)
GOLD = RGBColor(0xC9, 0x8A, 0x1F)
GOLD_BG = RGBColor(0xFD, 0xF3, 0xE3)
DARK = RGBColor(0x26, 0x26, 0x26)
GREY = RGBColor(0x6B, 0x6B, 0x6B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TOTAL = 11

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def box(slide, l, t, w, h, fill=None, line=None):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t),
                                Inches(w), Inches(h))
    sp.line.fill.background()
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is not None:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    return sp


def card(slide, l, t, w, h, number, label):
    sp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l),
                                Inches(t), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = NAVY
    sp.line.fill.background()
    try:
        sp.adjustments[0] = 0.12
    except Exception:
        pass
    tf = sp.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = number
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = "Calibri"
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = label
    r2.font.size = Pt(12)
    r2.font.color.rgb = GOLD
    r2.font.name = "Calibri"
    return sp


def textbox(slide, l, t, w, h):
    return slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w),
                                    Inches(h))


def footer(slide, n):
    ft = textbox(slide, 0.6, 7.02, 12.13, 0.35)
    p = ft.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Failures — Final Year Project Defence"
    r.font.size = Pt(10)
    r.font.color.rgb = GREY
    r.font.name = "Calibri"
    p2 = textbox(slide, 11.4, 7.02, 1.33, 0.35)
    p2.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT
    r = p2.text_frame.paragraphs[0].add_run()
    r.text = f"{n:02d} / {TOTAL}"
    r.font.size = Pt(10)
    r.font.color.rgb = GREY
    r.font.name = "Calibri"


def header(slide, n, kicker, title):
    kb = textbox(slide, 0.6, 0.22, 12.1, 0.32)
    p = kb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = kicker.upper()
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = GOLD
    r.font.name = "Calibri"
    tb = textbox(slide, 0.6, 0.52, 12.1, 0.75)
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.size = Pt(27)
    r.font.bold = True
    r.font.color.rgb = NAVY
    r.font.name = "Calibri"
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6),
                                  Inches(1.32), Inches(1.6), Pt(3))
    rule.fill.solid()
    rule.fill.fore_color.rgb = GOLD
    rule.line.fill.background()
    footer(slide, n)


def bullets(slide, l, t, w, h, items, size=17, gap=8):
    tx = textbox(slide, l, t, w, h)
    for i, b in enumerate(items):
        p = tx.text_frame.paragraphs[0] if i == 0 else tx.text_frame.add_paragraph()
        p.space_after = Pt(gap)
        parts = b.split("||")
        mk = p.add_run()
        mk.text = "▸ "
        mk.font.size = Pt(size)
        mk.font.bold = True
        mk.font.color.rgb = GOLD
        mk.font.name = "Calibri"
        for j, part in enumerate(parts):
            r = p.add_run()
            r.text = part
            r.font.size = Pt(size)
            r.font.color.rgb = DARK
            r.font.name = "Calibri"
            if j % 2 == 0 and len(parts) > 1:
                pass
        # gold-highlight segments are wrapped in @@...@@
        for run in p.runs:
            if "@@" in run.text:
                run.text = run.text.replace("@@", "")
                run.font.bold = True
                run.font.color.rgb = NAVY
    return tx


def strip(slide, text):
    box(slide, 0.6, 6.35, 12.13, 0.55, fill=GOLD_BG)
    tx = textbox(slide, 0.85, 6.38, 11.6, 0.5)
    p = tx.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(13)
    r.font.italic = True
    r.font.color.rgb = NAVY
    r.font.name = "Calibri"


def notes(slide, text):
    slide.notes_slide.placeholders[1].text_frame.text = text


def img(slide, fname, l, t, w, h):
    slide.shapes.add_picture(str(FIG / fname), Inches(l), Inches(t),
                             width=Inches(w), height=Inches(h))


# ---------------------------------------------------------------- 1 title
s = prs.slides.add_slide(BLANK)
box(s, 0, 0, 13.33, 7.5, fill=NAVY)
box(s, 0, 0, 13.33, 0.09, fill=GOLD)
tb = textbox(s, 1.0, 0.7, 11.33, 0.4)
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "MIVA OPEN UNIVERSITY  ·  SCHOOL OF COMPUTING"
r.font.size = Pt(13)
r.font.color.rgb = GOLD
r.font.name = "Calibri"
lines = ["DESIGN AND IMPLEMENTATION OF A DETERMINISTIC",
         "FAILURE-MODE GUARDRAIL SYSTEM FOR AI-GENERATED",
         "SOFTWARE USING MODEL CONTEXT PROTOCOL"]
tb = textbox(s, 1.0, 1.45, 11.33, 3.0)
for i, t in enumerate(lines):
    p = tb.text_frame.paragraphs[0] if i == 0 else tb.text_frame.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = t
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = "Calibri"
    p.space_after = Pt(2)
badge = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.4),
                           Inches(4.55), Inches(2.53), Inches(0.55))
badge.fill.solid()
badge.fill.fore_color.rgb = GOLD
badge.line.fill.background()
try:
    badge.adjustments[0] = 0.5
except Exception:
    pass
p = badge.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "2023/C/SENG/0351"
r.font.size = Pt(15)
r.font.bold = True
r.font.color.rgb = NAVY
r.font.name = "Calibri"
tb = textbox(s, 1.0, 5.35, 11.33, 1.8)
for t in ["OLUWAMAYOWA KALEJAIYE",
          "Supervisor: Ijegwa Acheme, Ph.D   ·   July, 2026"]:
    p = tb.text_frame.paragraphs[0] if t.startswith("OLUW") else tb.text_frame.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = t
    r.font.size = Pt(17) if t.startswith("OLUW") else Pt(14)
    r.font.bold = t.startswith("OLUW")
    r.font.color.rgb = WHITE
    r.font.name = "Calibri"
    p.space_after = Pt(4)

# ---------------------------------------------------------------- 2 problem
s = prs.slides.add_slide(BLANK)
header(s, 2, "01 · Problem", "Agents write code that runs — not code that survives")
bullets(s, 0.6, 1.65, 12.13, 4.4, [
    "Coding agents learn from @@tutorials@@, which never show the failure.",
    "Benchmarks score @@correctness on exercised paths@@ — never resilience.",
    "Ambiguous outcomes (charged? lost?) become @@double charges@@ and @@lost work@@.",
    "No @@deterministic, evidence-backed guardrails@@ reach agents as tools.",
], size=19, gap=12)
strip(s, "A payment handler that passes every test and double-charges on retry is a success under every standard metric.")
notes(s, "Open with the double-charge story: provider charges, response is lost, handler retries blindly. Say: benchmarks never test this path. Pause, then the gap line.")

# ---------------------------------------------------------------- 3 aim
s = prs.slides.add_slide(BLANK)
header(s, 3, "02 · Aim", "Build the checking layer benchmarks never built")
bullets(s, 0.6, 1.65, 12.13, 4.9, [
    "@@Aim:@@ design, implement, and evaluate deterministic failure-mode guardrails for AI-generated software.",
    "1. Investigate failure modes and existing guardrail approaches.",
    "2. Design an invariant-based guardrail framework.",
    "3. Develop it as a @@Model Context Protocol@@ server.",
    "4. Implement a deterministic @@evaluation harness@@.",
    "5. Evaluate through @@proxy and blind agent studies@@.",
], size=18, gap=9)
notes(s, "Read the aim once, slowly. Walk the five objectives quickly; each maps to a chapter and to a results table later.")

# ---------------------------------------------------------------- 4 lit
s = prs.slides.add_slide(BLANK)
header(s, 4, "03 · Literature", "Everything exists except the connection")
bullets(s, 0.6, 1.65, 12.13, 4.4, [
    "Correctness benchmarks (HumanEval, SWE-bench) @@never score resilience@@.",
    "Pattern-selection DSS @@compare technologies@@ — they never check generated code.",
    "Resilience canons catalogue controls as @@knowledge, not as checks@@.",
    "Gap: @@nobody connects deterministic guardrails to the agents@@ producing the code.",
], size=19, gap=12)
strip(s, "Done A, B, C — but none done D. Therefore propose E.")
notes(s, "Name the three prior strands in one breath each. Land on the gap formula: done A/B/C, none done D, therefore propose E.")

# ---------------------------------------------------------------- 5 method
s = prs.slides.add_slide(BLANK)
header(s, 5, "04 · Method", "Build the artefact, then measure it")
bullets(s, 0.6, 1.65, 5.6, 4.4, [
    "@@Design Science Research:@@ build, then evaluate — not surveys, not opinion.",
    "@@Agile:@@ rules, tools, and harness co-evolved through iterations.",
    "@@Data:@@ 17 matched pairs + 6 proxy + 6 adversarial cases.",
    "@@Instrument:@@ one harness, ten criteria, frozen prompts and manifests.",
], size=18, gap=10)
card(s, 7.0, 1.7, 2.75, 1.9, "17", "matched pairs")
card(s, 10.0, 1.7, 2.75, 1.9, "10", "scored criteria")
card(s, 7.0, 3.85, 2.75, 1.9, "6+6", "scenarios + adversarial")
card(s, 10.0, 3.85, 2.75, 1.9, "3", "commercial agents")
notes(s, "If asked why not surveys: opinions about resilience are a poor substitute for measured findings on code. Say that only if pushed.")

# ---------------------------------------------------------------- 6 arch
s = prs.slides.add_slide(BLANK)
header(s, 6, "05 · System", "One server, any agent, zero token cost")
bullets(s, 0.6, 1.65, 5.6, 4.4, [
    "@@Knowledge base:@@ 11 principles, 10 rule families, versioned JSON.",
    "@@Deterministic engine:@@ review and score — never hallucinates.",
    "@@13 MCP tools:@@ any compliant agent calls them; findings carry evidence.",
], size=18, gap=10)
img(s, "fig31_architecture.png", 6.7, 1.6, 6.0, 4.5)
notes(s, "Walk left to right across the diagram. Emphasise: one server, any agent; the check costs nothing and never varies.")

# ---------------------------------------------------------------- 7 eval
s = prs.slides.add_slide(BLANK)
header(s, 7, "06 · Evaluation", "One variable changed, everything else frozen")
bullets(s, 0.6, 1.65, 5.6, 4.4, [
    "Same @@6 prompts@@, two arms: baseline vs guardrails connected.",
    "@@Claude, Cursor, Codex@@ — 17 matched pairs, no per-agent tuning.",
    "Frozen @@prompt hashes, manifests, commits@@ — fully reproducible.",
], size=18, gap=10)
img(s, "fig34_eval_flow.png", 6.7, 1.7, 6.0, 3.4)
notes(s, "Stress the single manipulated variable: the only difference between arms is whether the server was connected.")

# ---------------------------------------------------------------- 8 proxy
s = prs.slides.add_slide(BLANK)
header(s, 8, "07 · Results I", "The instrument sees improvement where it exists")
bullets(s, 0.6, 1.65, 5.6, 3.6, [
    "CRITICAL @@7 → 3@@, HIGH @@7 → 0@@ across six scenarios.",
    "Payment and webhook: @@3 → 0@@ CRITICAL each.",
    "Architecture @@1.0 throughout@@ — nothing bought with infrastructure.",
], size=18, gap=10)
img(s, "fig41_proxy.png", 6.7, 1.6, 6.0, 4.3)
strip(s, "This qualifies the harness — so trust it on the blind study next.")
notes(s, "This slide qualifies the instrument: the harness sees improvement where improvement exists, so trust it on the blind study next.")

# ---------------------------------------------------------------- 9 agents
s = prs.slides.add_slide(BLANK)
header(s, 9, "08 · Results II", "Consistent direction across all three agents")
bullets(s, 0.6, 1.65, 5.6, 3.6, [
    "@@16 of 17@@ pairs improved on at least one criterion.",
    "HIGH findings @@never rose@@ — and fell 13 → 1 overall.",
    "Adversarial probe: @@4 of 6@@ flagged at CRITICAL; limits documented.",
], size=18, gap=10)
img(s, "fig42_agents.png", 6.7, 1.6, 6.0, 4.3)
strip(s, "Direction holds per agent: 6/6, 5/5, 5/6 — no single model carries it.")
notes(s, "The headline slide. Say the three numbers slowly. If asked about the regressions: one is the documented upsert false positive, the rest are the tool catching unsafe retries the agent added.")

# ---------------------------------------------------------------- 10 discuss
s = prs.slides.add_slide(BLANK)
header(s, 10, "09 · Discussion", "Three lessons, five objectives met")
bullets(s, 0.6, 1.65, 5.9, 4.4, [
    "@@Checks beat judges:@@ deterministic output cannot hallucinate.",
    "@@Early beats late:@@ plan review reshaped designs; code review patched them.",
    "@@More code is the mechanism:@@ +39% volume is pending records and reconciliation — the resilience itself.",
], size=18, gap=10)
rows, cols = 6, 3
left, top, w, h = Inches(6.8), Inches(3.1), Inches(5.9), Inches(2.6)
gt = s.shapes.add_table(rows, cols, left, top, w, h).table
cells = [["Objective", "Evidence", "Met"],
         ["1 Investigate", "Ch. 2, Table 2.1", "Yes"],
         ["2 Design", "Ch. 3, Figs 3.1–3.2", "Yes"],
         ["3 Develop", "Ch. 4, server + tools", "Yes"],
         ["4 Harness", "Ch. 3–4, 10 criteria", "Yes"],
         ["5 Evaluate", "Tables 4.2–4.4", "Yes"]]
for i in range(rows):
    for j in range(cols):
        c = gt.cell(i, j)
        c.text = ""
        c.vertical_anchor = 1
        p = c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if j == 2 else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = cells[i][j]
        r.font.size = Pt(12)
        r.font.name = "Calibri"
        r.font.bold = (i == 0)
        r.font.color.rgb = WHITE if i == 0 else DARK
        if i == 0:
            c.fill.solid()
            c.fill.fore_color.rgb = NAVY
notes(s, "Three lessons, one breath each. The objectives table is in the report; here just assert the mapping confidently.")

# ---------------------------------------------------------------- 11 close
s = prs.slides.add_slide(BLANK)
header(s, 11, "10 · Conclusion", "A cheap, reproducible floor for resilience practice")
bullets(s, 0.6, 1.65, 12.13, 3.1, [
    "Deterministic guardrails @@measurably improve@@ agent-generated resilience.",
    "Recommend: review @@plans before code@@; ship checks as @@tools, not judges@@.",
    "Next: @@AST-level rules@@, enforced tool use, live-provider testing.",
], size=19, gap=10)
links = [("github.com/mayowa-kalejaiye/Failures", 0.6),
         ("doi.org/10.5281/zenodo.22966362", 4.75),
         ("failures-mcp on PyPI", 8.9)]
for text, l in links:
    b = s.shapes.add_shape(5, Inches(l), Inches(5.35), Inches(3.85),
                           Inches(0.62))
    b.fill.solid()
    b.fill.fore_color.rgb = NAVY
    b.line.fill.background()
    try:
        b.adjustments[0] = 0.5
    except Exception:
        pass
    p = b.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size = Pt(13)
    r.font.color.rgb = WHITE
    r.font.name = "Calibri"
tb = textbox(s, 0.6, 6.2, 12.13, 0.6)
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "Thank you."
r.font.size = Pt(22)
r.font.bold = True
r.font.color.rgb = NAVY
r.font.name = "Calibri"
notes(s, "End on the artifact: code, paper, DOI all public. Then stop talking and take questions. If asked about limits, go straight to the adversarial boundary — owning it is the strongest move.")

prs.save(str(OUT))
print(f"Saved {OUT} — {len(prs.slides)} slides")
