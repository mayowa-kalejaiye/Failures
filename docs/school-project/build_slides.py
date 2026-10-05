"""Defence slides for the Failures final-year project. 16:9, 11 slides."""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
OUT = ROOT / "FAILURES_Defence_Slides.pptx"

NAVY = RGBColor(0x1F, 0x38, 0x64)
DARK = RGBColor(0x33, 0x33, 0x33)
GREY = RGBColor(0x59, 0x56, 0x59)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def textbox(slide, left, top, width, height):
    return slide.shapes.add_textbox(Inches(left), Inches(top),
                                    Inches(width), Inches(height))


def title_slide(title_lines, sub_lines):
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    tb = textbox(s, 1.0, 1.2, 11.33, 3.2)
    for i, t in enumerate(title_lines):
        p = tb.text_frame.paragraphs[0] if i == 0 else tb.text_frame.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = t
        r.font.size = Pt(30 if i == 0 else 24)
        r.font.bold = True
        r.font.color.rgb = WHITE
        r.font.name = "Calibri"
        p.space_after = Pt(6)
    tb2 = textbox(s, 1.0, 4.8, 11.33, 2.2)
    for t in sub_lines:
        p = tb2.text_frame.paragraphs[0] if t == sub_lines[0] else tb2.text_frame.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = t
        r.font.size = Pt(15)
        r.font.color.rgb = WHITE
        r.font.name = "Calibri"
        p.space_after = Pt(4)
    return s


def content_slide(title, bullets, notes="", image=None, img_box=None):
    s = prs.slides.add_slide(BLANK)
    tb = textbox(s, 0.6, 0.25, 12.1, 1.0)
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = NAVY
    r.font.name = "Calibri"
    rule = s.shapes.add_shape(1, Inches(0.6), Inches(1.15), Inches(12.1),
                              Pt(2))
    rule.fill.solid()
    rule.fill.fore_color.rgb = NAVY
    rule.line.fill.background()
    if image:
        tx = textbox(s, 0.6, 1.5, 5.8, 5.2)
        for i, b in enumerate(bullets):
            p = tx.text_frame.paragraphs[0] if i == 0 else tx.text_frame.add_paragraph()
            p.level = 0
            p.space_after = Pt(10)
            r = p.add_run()
            r.text = b
            r.font.size = Pt(17)
            r.font.color.rgb = DARK
            r.font.name = "Calibri"
        l, t, w, h = img_box
        s.shapes.add_picture(str(FIG / image), Inches(l), Inches(t),
                             width=Inches(w), height=Inches(h))
    else:
        tx = textbox(s, 0.6, 1.5, 12.1, 5.2)
        for i, b in enumerate(bullets):
            p = tx.text_frame.paragraphs[0] if i == 0 else tx.text_frame.add_paragraph()
            p.level = 0
            p.space_after = Pt(10)
            r = p.add_run()
            r.text = b
            r.font.size = Pt(18)
            r.font.color.rgb = DARK
            r.font.name = "Calibri"
    ft = textbox(s, 0.6, 7.05, 12.1, 0.35)
    p = ft.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Failures — Final Year Project Defence"
    r.font.size = Pt(11)
    r.font.color.rgb = GREY
    r.font.name = "Calibri"
    if notes:
        s.notes_slide.placeholders[1].text_frame.text = notes
    return s


TITLE = ["DESIGN AND IMPLEMENTATION OF A DETERMINISTIC",
         "FAILURE-MODE GUARDRAIL SYSTEM FOR AI-GENERATED",
         "SOFTWARE USING MODEL CONTEXT PROTOCOL"]
SUB = ["OLUWAMAYOWA KALEJAIYE  —  2023/C/SENG/0351",
       "Department of Software Engineering, School of Computing, Miva Open University",
       "Supervisor: Ijegwa Acheme, Ph.D   —   July, 2026"]

title_slide(TITLE, SUB)

content_slide(
    "The problem",
    ["Coding agents write happy-path code: tutorials never show the failure.",
     "Benchmarks score correctness on exercised paths, never resilience.",
     "Ambiguous outcomes (charged? lost?) become double charges and lost work.",
     "No deterministic, evidence-backed guardrails reach agents as tools."],
    notes=("Open with the double-charge story: provider charges, response is "
           "lost, handler retries blindly. Say: benchmarks never test this "
           "path. Pause, then the gap line.")),

content_slide(
    "Aim and objectives",
    ["Aim: design, implement, and evaluate deterministic failure-mode guardrails for AI-generated software.",
     "1. Investigate failure modes and existing guardrail approaches.",
     "2. Design an invariant-based guardrail framework.",
     "3. Develop it as a Model Context Protocol server.",
     "4. Implement a deterministic evaluation harness.",
     "5. Evaluate through proxy and blind agent studies."],
    notes=("Read the aim once, slowly. Walk the five objectives quickly; "
           "each maps to a chapter and to a results table later.")),

content_slide(
    "Literature and the gap",
    ["What exists: correctness benchmarks, pattern-selection DSS, resilience canons.",
     "What is missing: checks on failure properties of generated code.",
     "Nobody connects deterministic guardrails to the agents producing the code.",
     "Therefore this study builds and measures that connection."],
    notes=("Name the three prior strands in one breath each. Land on the "
           "gap formula: done A/B/C, none done D, therefore propose E.")),

content_slide(
    "Methodology",
    ["Research design: Design Science Research — build the artefact, then measure it.",
     "Development: Agile iterations — rules, tools, harness, each tested before the next.",
     "Data: 17 matched agent pairs + 6 proxy pairs + 6 adversarial cases.",
     "Instrument: one deterministic harness, ten criteria, frozen prompts and manifests."],
    notes=("If asked why not surveys: opinions about resilience are a poor "
           "substitute for measured findings on code. Say that only if pushed.")),

content_slide(
    "System architecture",
    ["Knowledge base: 11 principles, 10 rule families, versioned JSON.",
     "Deterministic engine: review, score, never hallucinates.",
     "13 MCP tools: any compliant agent can call them at zero token cost."],
    notes=("Walk left to right across the diagram. Emphasise: one server, "
           "any agent; the check costs nothing and never varies."),
    image="fig31_architecture.png", img_box=(6.7, 1.5, 6.0, 4.6)),

content_slide(
    "How evaluation works",
    ["Same 6 prompts, two arms: baseline vs guardrails connected.",
     "Three agents: Claude, Cursor, Codex — 17 matched pairs.",
     "One harness scores all: findings, invariants, proportionality."],
    notes=("Stress the single manipulated variable: the only difference "
           "between arms is whether the server was connected."),
    image="fig34_eval_flow.png", img_box=(6.7, 1.6, 6.0, 3.6)),

content_slide(
    "Results I — proxy study",
    ["CRITICAL 7 → 3, HIGH 7 → 0 across six scenarios.",
     "Payment and webhook: 3 → 0 CRITICAL each.",
     "Architecture quality 1.0 throughout: nothing bought with infrastructure."],
    notes=("This slide qualifies the instrument: the harness sees "
           "improvement where improvement exists, so trust it on the blind "
           "study next."),
    image="fig41_proxy.png", img_box=(6.7, 1.6, 6.0, 4.4)),

content_slide(
    "Results II — blind agent study",
    ["16 of 17 pairs improved on at least one criterion.",
     "HIGH findings never rose in any pair — and fell 13 → 1 overall.",
     "Adversarial probe: 4 of 6 flagged at CRITICAL; limits documented."],
    notes=("The headline slide. Say the three numbers slowly. If asked about "
           "the regressions: one is the documented upsert false positive, "
           "the rest are the tool catching unsafe retries the agent added."),

    image="fig42_agents.png", img_box=(6.7, 1.6, 6.0, 4.2)),

s10 = content_slide(
    "Discussion and objectives check",
    ["Checks beat judges: deterministic output cannot hallucinate.",
     "Early beats late: plan review reshaped designs; code review patched them.",
     "All five objectives met — each maps to evidence in Chapter 4."],
    notes=("Three lessons, one breath each. The objectives table is in the "
           "report; here just assert the mapping confidently."))
# objectives mini-table on slide 10
rows, cols = 6, 3
left, top, w, h = Inches(6.7), Inches(4.3), Inches(6.0), Inches(2.4)
gt = s10.shapes.add_table(rows, cols, left, top, w, h).table
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
        p = c.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = cells[i][j]
        r.font.size = Pt(13)
        r.font.name = "Calibri"
        r.font.bold = (i == 0)
        r.font.color.rgb = WHITE if i == 0 else DARK
        if i == 0:
            c.fill.solid()
            c.fill.fore_color.rgb = NAVY

content_slide(
    "Conclusion",
    ["Deterministic guardrails measurably improve agent-generated resilience.",
     "Recommend: review plans before code; ship checks as tools, not judges.",
     "Next: AST-level rules, enforced tool use, live-provider testing.",
     "Artifact: github.com/mayowa-kalejaiye/Failures — thank you."],
    notes=("End on the artifact: code, paper, DOI all public. Then stop "
           "talking and take questions. If asked about limits, go straight "
           "to the adversarial boundary — owning it is the strongest move."))

prs.save(str(OUT))
print(f"Saved {OUT} — {len(prs.slides)} slides")
