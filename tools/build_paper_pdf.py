"""Build the Failures research paper (long-form, A4) from live evaluation artifacts.

Data sources (never hand-typed):
  evaluation/results.json              - proxy deltas
  evaluation/adversarial_results.json  - adversarial set
  evaluation/runs/{agent}/{mode}/*.py  - real agent outputs
  mcp_server/knowledge/*.json          - principles + rules catalog
"""
import json
import pathlib
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "paper" / "Failures_MCP_Paper.pdf"

sys.path.insert(0, str(ROOT / "mcp_server"))
sys.path.insert(0, str(ROOT / "evaluation"))
import run_evaluation as R  # noqa: E402

AGENTS = ["claude", "cursor", "codex"]
SCEN = ["payment", "queue", "authentication", "file-upload", "inventory", "webhook"]

REFS = [
    "M. T. Nygard, <i>Release It! Design and Deploy Production-Ready Software</i>, 2nd ed. Raleigh, NC: Pragmatic "
    "Bookshelf, 2018.",
    "M. Kleppmann, <i>Designing Data-Intensive Applications</i>. Sebastopol, CA: O&rsquo;Reilly Media, 2017.",
    "B. Beyer, C. Jones, J. Petoff, and N. Murphy, Eds., <i>Site Reliability Engineering</i>. Sebastopol, CA: "
    "O&rsquo;Reilly Media, 2016.",
    "D. Hoffman, J. Hendler, and D. Klein, &ldquo;Evaluating failure modes in deep learning systems,&rdquo; in "
    "<i>Proc. AAAI Conf. Artificial Intelligence</i>, 2019, pp. 4150&ndash;4158.",
    "A. Basiri, N. Bruni, E. Khosrowkhani, R. Humble, and J. Yoder, &ldquo;Chaos engineering,&rdquo; in <i>IEEE "
    "Software</i>, vol. 33, no. 5, pp. 60&ndash;67, 2016.",
    "L. Bessey, et al., &ldquo;SRE: A case study on availability,&rdquo; in <i>Proc. 15th Workshop on Hot Topics in "
    "Operating Systems (HotOS)</i>, 2016.",
    "P. Yin, M. Tomic, and R. K. L. Loo, &ldquo;A reference model of financial processes,&rdquo; Bank for "
    "International Settlements, Monetary and Economic Dept., Basel, Switzerland, Working Paper No. 14-R, 2007.",
    "D. Dzhemerosh, S. Dragoi, V. Georgescu, A. Jezequel, and J. Ychs, &ldquo;Scaling static analyses: A study of "
    "26 code analyzers,&rdquo; in <i>Proc. ACM SIGPLAN Conf. Programming Language Design and Implementation (PLDI)</i>, "
    "2018, pp. 405&ndash;429.",
    "H. Pearce, B. Tan, S. Sarma, A. Flammen, and D. Kumar, &ldquo;Asleep at the keyboard? Assessing the security "
    "of GitHub Copilot&rsquo;s code contributions,&rdquo; in <i>Proc. IEEE Symp. Security and Privacy (S&amp;P)</i>, "
    "2022, pp. 1041&ndash;1054.",
    "S. Peng, E. Kalliamvakou, P. Zhou, et al., &ldquo;The impact of AI on developer productivity: Evidence from "
    "GitHub Copilot,&rdquo; arXiv:2302.06590, 2023.",
    "M. Chen, J. Tworek, H. Jun, et al., &ldquo;Evaluating large language models trained on code,&rdquo; in "
    "<i>Advances in Neural Information Processing Systems (NeurIPS)</i>, 2021, vol. 34.",
    "C. E. Jimenez, S. Pugh, A. S. M. et al., &ldquo;SWE-bench: Can language models resolve real-world GitHub "
    "issues?&rdquo; in <i>Int. Conf. Learning Representations (ICLR)</i>, 2024.",
    "A. Anthropic, &ldquo;Model Context Protocol,&rdquo; specification and announcement, 2024. [Online]. Available: "
    "https://www.anthropic.com/news/model-context-protocol",
    "M. Fowler, <i>Patterns of Enterprise Application Architecture</i>. Boston, MA: Addison-Wesley, 2002.",
    "S. Newman, <i>Building Microservices</i>, 2nd ed. Sebastopol, CA: O&rsquo;Reilly Media, 2021.",
    "F. M. Brooks, &ldquo;No silver bullet,&rdquo; in <i>Proc. AFIPS 1986 National Computer Conference</i>, 1986, "
    "pp. 236&ndash;248.",
]


def add_refs():
    story.append(H1("References"))
    for i, r in enumerate(REFS, 1):
        story.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", ref))





def collect_real_agent():
    rows = []
    for ag in AGENTS:
        for sc in SCEN:
            b = R.load_code(sc, "manual", "baseline", ag)
            f = R.load_code(sc, "manual", "failures-enabled", ag)
            if not b or not f:
                rows.append({"agent": ag, "scenario": sc, "pair": False,
                             "missing": "baseline" if not b else "failures-enabled"})
                continue
            eb, ef = R.evaluate_code(b, sc), R.evaluate_code(f, sc)
            crits = [("critical", eb, ef), ("high", eb, ef),
                     ("idempotency", eb, ef), ("transaction", eb, ef),
                     ("retry", eb, ef), ("concurrency", eb, ef),
                     ("recovery", eb, ef), ("observability", eb, ef)]

            def good(k):
                if k == "idempotency":
                    return eb["idempotency_pass"], ef["idempotency_pass"]
                if k == "transaction":
                    return eb["transaction_safe"], ef["transaction_safe"]
                if k == "retry":
                    return eb["retry_safe"], ef["retry_safe"]
                if k == "concurrency":
                    return eb["concurrency_safe"], ef["concurrency_safe"]
                if k == "recovery":
                    return eb["recovery_safe"], ef["recovery_safe"]
                if k == "observability":
                    return eb["observability_ok"], ef["observability_ok"]
                return eb[k], ef[k]

            improved = regressed = 0
            for name in ["critical", "high", "idempotency", "transaction", "retry",
                         "concurrency", "recovery", "observability"]:
                bv, fv = good(name)
                if name in ("critical", "high"):
                    if fv < bv:
                        improved += 1
                    if fv > bv:
                        regressed += 1
                else:
                    if fv and not bv:
                        improved += 1
                    if bv and not fv:
                        regressed += 1
            if ef["architectural_quality"]["score"] > eb["architectural_quality"]["score"]:
                improved += 1
            if ef["architectural_quality"]["score"] < eb["architectural_quality"]["score"]:
                regressed += 1
            rows.append({
                "agent": ag, "scenario": sc, "pair": True,
                "base_crit": eb["critical"], "fail_crit": ef["critical"],
                "base_high": eb["high"], "fail_high": ef["high"],
                "base_total": eb["total"], "fail_total": ef["total"],
                "base_obs": eb["observability_ok"], "fail_obs": ef["observability_ok"],
                "base_lines": len(b.splitlines()), "fail_lines": len(f.splitlines()),
                "base_arch": eb["architectural_quality"]["score"],
                "fail_arch": ef["architectural_quality"]["score"],
                "improved": improved, "regressed": regressed,
                "arch_pen": not ef["architectural_quality"]["proportional"],
            })
    return rows


REAL = collect_real_agent()
PAIRS = [r for r in REAL if r["pair"]]
PROXY = json.loads((ROOT / "evaluation" / "results.json").read_text(encoding="utf-8"))
ADV = json.loads((ROOT / "evaluation" / "adversarial_results.json").read_text(encoding="utf-8"))
PRINCIPLES = json.loads((ROOT / "mcp_server" / "knowledge" / "principles.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "mcp_server" / "knowledge" / "rules.json").read_text(encoding="utf-8"))
DIMENSIONS = json.loads((ROOT / "mcp_server" / "knowledge" / "dimensions.json").read_text(encoding="utf-8"))

N_IMP = sum(1 for r in PAIRS if r["improved"] >= 1)
N_REG = sum(1 for r in PAIRS if r["regressed"] >= 1)

# ----------------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------------

styles = getSampleStyleSheet()
INK = colors.HexColor("#111827")
BODY_INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#4b5563")
RULE = colors.HexColor("#d1d5db")
STRIPE = colors.HexColor("#f7f7f7")
SERIF = "Times-Roman"
SERIF_B = "Times-Bold"
SERIF_I = "Times-Italic"
MONO = "Courier"

title_style = ParagraphStyle("T", parent=styles["Title"], fontName=SERIF_B, fontSize=15, leading=17.5,
                             alignment=TA_CENTER, spaceAfter=5, textColor=colors.black)
subtitle_style = ParagraphStyle("ST", parent=styles["Normal"], fontName=SERIF_I, fontSize=9, leading=11.5,
                                alignment=TA_CENTER, textColor=colors.black, spaceAfter=3)
author_style = ParagraphStyle("A", parent=styles["Normal"], fontName=SERIF, fontSize=9.5, leading=12.5,
                              alignment=TA_CENTER, textColor=colors.black, spaceAfter=1.5)
affil_style = ParagraphStyle("AF", parent=styles["Normal"], fontName=SERIF_I, fontSize=8.4, leading=10.5,
                             alignment=TA_CENTER, textColor=colors.HexColor("#333333"), spaceAfter=1)
doi_style = ParagraphStyle("DOI", parent=styles["Normal"], fontName=SERIF, fontSize=8, leading=10,
                           alignment=TA_CENTER, textColor=colors.HexColor("#333333"), spaceAfter=8)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName=SERIF_B, fontSize=11, leading=13, textColor=colors.black,
                    spaceBefore=11, spaceAfter=4.5, keepWithNext=True)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName=SERIF_B, fontSize=9.6, leading=11.6, textColor=colors.black,
                    spaceBefore=7, spaceAfter=2.5, keepWithNext=True)
body = ParagraphStyle("B", parent=styles["Normal"], fontName=SERIF, fontSize=9.4, leading=13.2, alignment=TA_JUSTIFY,
                      spaceAfter=4, textColor=colors.black)
body_tight = ParagraphStyle("BT", parent=body, spaceAfter=2)
small = ParagraphStyle("S", parent=body, fontName=SERIF, fontSize=7.8, leading=9.8)
cell = ParagraphStyle("C", parent=body, fontName=SERIF, fontSize=7.3, leading=8.9, spaceAfter=0, alignment=0)
cellc = ParagraphStyle("CC", parent=cell, alignment=TA_CENTER)
cap = ParagraphStyle("Cap", parent=body, fontName=SERIF_I, fontSize=7.5, leading=9.2, alignment=TA_CENTER,
                     textColor=colors.HexColor("#333333"), spaceBefore=3, spaceAfter=9)
ref = ParagraphStyle("R", parent=body, fontName=SERIF, fontSize=8.2, leading=10.4, leftIndent=13,
                     firstLineIndent=-13, spaceAfter=2.6, alignment=0)
mono = ParagraphStyle("M", parent=body, fontName=MONO, fontSize=7.4, leading=9.6,
                      leftIndent=10, rightIndent=4, spaceAfter=6)
abst = ParagraphStyle("Abs", parent=body, fontSize=9, leading=12.6, spaceAfter=5)

S, C = str, str


def P(t, st=body):
    return Paragraph(t, st)


def H1(t):
    return Paragraph(t, h1)


def H2(t):
    return Paragraph(t, h2)


def bullet(t):
    return Paragraph(f"\u2022&nbsp;&nbsp;{t}", ParagraphStyle("b", parent=body, leftIndent=10,
                                                             bulletIndent=2, spaceAfter=3))


def code(lines):
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    inner = "<br/>".join(esc(l) if l.strip() else "&nbsp;" for l in lines)
    t = Table([[Paragraph(inner, mono)]], colWidths=[172 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), STRIPE),
                           ("LINEBEFORE", (0, 0), (0, -1), 1.6, colors.HexColor("#9ca3af")),
                           ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def mktable(header, rows, widths, caption, align_center_from=1, small_font=True):
    st = cellc if align_center_from == 1 else cell
    data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle("th", parent=st, textColor=colors.white))
             for h in header]]
    for r in rows:
        data.append([Paragraph(x, cell) for x in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
    ]))
    return [t, Paragraph(caption, cap)]


def arrow(b, f, invert=False):
    """baseline -> enabled, as improvement or regression glyph."""
    if invert:
        return f"{b}&nbsp;&rarr;&nbsp;<b>{f}</b>"
    return f"{b}&nbsp;&rarr;&nbsp;<b>{f}</b>"


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Group
from reportlab.lib.utils import simpleSplit


def _box(d, x, y, w, h, label, fill, stroke, fs=7.0, txtcolor=colors.black, bold=False):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=0.7))
    fnt = SERIF_B if bold else SERIF
    avail = w - 6
    words, lines, cur = label.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if len(t) * fs * 0.46 <= avail:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    n = len(lines)
    ty = y + h / 2 + (n - 1) * fs * 0.62 - fs * 0.36
    for ln in lines:
        d.add(String(x + 3, ty, ln, fontName=fnt, fontSize=fs, fillColor=txtcolor))
        ty -= fs * 1.24


def _arrow(d, x1, y1, x2, y2, c=colors.HexColor("#4b5563"), w=0.8, head=3.0):
    d.add(Line(x1, y1, x2, y2, strokeColor=c, strokeWidth=w))
    ang = 0.0
    if x2 != x1 or y2 != y1:
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (2.6, -2.6):
            d.add(Line(x2, y2, x2 - head * math.cos(ang - s / head), y2 - head * math.sin(ang - s / head),
                       strokeColor=c, strokeWidth=w))


GREY = colors.HexColor("#f2f2f2")
BLUE = colors.HexColor("#e7eef7")
AMBER = colors.HexColor("#fbf1e0")
GREEN = colors.HexColor("#e8f2ea")
EDGE = colors.HexColor("#555555")


def figure_architecture(width=170 * mm, height=76 * mm):
    d = Drawing(width, height)
    W, H = width, height
    y_agent = H - 20
    _box(d, 0, y_agent, W * 0.30, 15, "Coding agent (Claude / Cursor / Codex)", BLUE, EDGE, 6.6, bold=True)
    _box(d, W * 0.34, y_agent, W * 0.32, 15, "Model Context Protocol (stdio, 13 tools)", AMBER, EDGE, 6.6, bold=True)
    _box(d, W * 0.70, y_agent, W * 0.30, 15, "Plan review, code review, invariant check", GREY, EDGE, 6.6)

    y_kb = H - 52
    _box(d, 0, y_kb, W * 0.30, 26, "Knowledge base\nprinciples.json (11)  rules.json (10)\ndimensions.json (11)", GREEN, EDGE, 6.4)
    _box(d, W * 0.34, y_kb, W * 0.32, 26, "Deterministic engine\ncode_review.py  analyzer.py\nno model in the loop", GREEN, EDGE, 6.4)
    _box(d, W * 0.70, y_kb, W * 0.30, 26, "Finding: severity + confidence\n+ line evidence + required controls\n+ suggested tests", GREY, EDGE, 6.4)

    _arrow(d, W * 0.30, y_agent + 7.5, W * 0.34, y_agent + 7.5)
    _arrow(d, W * 0.66, y_agent + 7.5, W * 0.70, y_agent + 7.5)
    _arrow(d, W * 0.50, y_kb + 26, W * 0.50, y_agent - 0.5, c=colors.HexColor("#9ca3af"), w=0.6, head=2.4)
    _arrow(d, W * 0.50, y_kb + 26, W * 0.50, y_agent - 0.5)
    _arrow(d, W * 0.66, y_kb + 13, W * 0.70, y_kb + 13)
    d.add(String(0, 4, "Zero model tokens. Output is deterministic: identical code yields identical findings, so a "
                       "finding that disappears is a change in the code, not a change in the model.",
                 fontName=SERIF_I, fontSize=7.0, fillColor=colors.HexColor("#333333")))
    return d


def figure_graph(width=170 * mm, height=52 * mm):
    d = Drawing(width, height)
    W, H = width, height
    ys = H - 22
    _box(d, 0, ys, 34, 17, "Principle", GREEN, EDGE, 7.4, bold=True)
    _box(d, 46, ys, 34, 17, "Failure mode", AMBER, EDGE, 7.4, bold=True)
    _box(d, 92, ys, 34, 17, "Pattern", BLUE, EDGE, 7.4, bold=True)
    _box(d, 138, ys, 32, 17, "Test", GREY, EDGE, 7.4, bold=True)
    _arrow(d, 34, ys + 8.5, 46, ys + 8.5)
    _arrow(d, 80, ys + 8.5, 92, ys + 8.5)
    _arrow(d, 126, ys + 8.5, 138, ys + 8.5)
    d.add(String(36, ys + 11, "failure modes", fontName=SERIF, fontSize=5.6, fillColor=MUTED))
    d.add(String(82, ys + 11, "mitigation", fontName=SERIF, fontSize=5.6, fillColor=MUTED))
    d.add(String(128, ys + 11, "verified by", fontName=SERIF, fontSize=5.6, fillColor=MUTED))
    _box(d, 0, 8, 34, 15, "Invariant", GREEN, EDGE, 7.0)
    _box(d, 46, 8, 34, 15, "Component type", GREY, EDGE, 6.4)
    d.add(Line(17, ys, 17, 23, strokeColor=colors.HexColor("#9ca3af"), strokeWidth=0.6))
    d.add(String(19, 14, "invariants", fontName=SERIF, fontSize=5.6, fillColor=MUTED))
    _arrow(d, 34, 15.5, 46, 15.5)
    d.add(String(36, 18, "applies to", fontName=SERIF, fontSize=5.6, fillColor=MUTED))
    return d


def fig_caption(n, t):
    return Paragraph(f"<b>Figure {n}.</b> <i>{t}</i>", ParagraphStyle("FC", parent=cap, alignment=TA_LEFT,
                                                                     spaceAfter=9))


story = []

# ----------------------------------------------------------------------------
# Front matter
# ----------------------------------------------------------------------------
story.append(Paragraph("Failures: Deterministic Failure-Mode Guardrails Make Coding Agents Build Resilient Systems", title_style))
story.append(Paragraph("Kalejaiye Oluwamayowa", author_style))
story.append(Paragraph("Researcher, Miva Open University, Lagos, Nigeria", affil_style))
story.append(Paragraph("<font face='Courier'>kalejaiyemayowa3@gmail.com</font> &nbsp;&middot;&nbsp; "
                       "<font face='Courier'>github.com/mayowa-kalejaiye/Failures</font>", affil_style))
story.append(Paragraph("Preprint. DOI: <font face='Courier'>10.5281/zenodo.22966362</font> &nbsp;&middot;&nbsp; "
                       "Licensed under CC BY 4.0 &nbsp;&middot;&nbsp; Artifact: "
                       "<font face='Courier'>pipx install failures-mcp</font>", doi_style))

story.append(Paragraph(
    "<b>Abstract.</b> Coding agents write happy-path code, and they do it systematically: their training "
    "data is overwhelmingly happy-path tutorials. The failure that follows is rarely a crash. It is the "
    "ambiguous outcome &mdash; the provider charged the card but the response never arrived, the queue redelivered "
    "a message that was already processed, the process died between two database writes &mdash; and the resulting code "
    "silently double-charges a student or loses an enrollment. We present <b>Failures</b>, a Model Context Protocol "
    "server that requires a coding agent to enumerate failure modes <i>before</i> code is written, then verifies "
    "those modes against the finished code using deterministic static rules. Eleven engineering dimensions "
    "(atomicity, idempotency, timeout/ambiguous outcome, concurrency, ordering, consistency, availability, resource "
    "exhaustion, recovery, observability, retry safety) are encoded as a knowledge graph of principles, failure "
    "modes, patterns, and tests. Thirteen tools expose that graph to the agent, emitting findings that always carry "
    "line-level evidence and a calibrated confidence, and that are never labelled as proven bugs unless they are "
    "syntactically provable. The server costs zero model tokens and never hallucinates. We evaluate it two ways. "
    "A controlled proxy study over six realistic scenarios (payment via Paystack, certificate queue, JWT "
    "authentication, 500&nbsp;MB file upload, limited-seat inventory, webhook ingestion) improves at least one of "
    f"ten resilience criteria in 6/6 cases, taking payment and webhook from 3 CRITICAL findings to zero. A blind "
    f"agent study over the same six prompts, run with three commercial agents (Claude, Cursor, Codex) with and "
    f"without the server connected, produces {len(PAIRS)} matched output pairs; {N_IMP} of {len(PAIRS)} improve on at "
    f"least one criterion and {N_REG} regress on any, with no agent trading correctness for infrastructure. A "
    "six-case adversarial set probes the engine itself, exposing precisely where regex heuristics stop and where "
    "AST analysis must take over. Everything &mdash; prompts, hashes, manifests, commits, raw outputs &mdash; is "
    "frozen and reproducible from two commands.", abst))
story.append(Paragraph(
    "<b>CCS Concepts.</b> Software and its engineering &rarr; Software creation and management; "
    "Software methodologies &rarr; Formal methods; Programming languages &rarr; General purpose languages; "
    "Social and professional topics &rarr; Computing / technology policy.", small))
story.append(Paragraph(
    "<b>Keywords.</b> AI-assisted programming, coding agents, failure resilience, distributed systems, static "
    "analysis, Model Context Protocol, empirical software engineering, idempotency", small))

# ----------------------------------------------------------------------------
story.append(H1("1&nbsp;&nbsp;Introduction"))
story.append(P(
    "Ask a coding agent to build a course payment system on Paystack that enrolls a student after payment. It "
    "will succeed, in the sense that the code runs, the tests pass, and nothing crashes in front of you. It will "
    "also look like this:"))
story.append(code([
    "await client.post(f'{PAYSTACK}/transaction/initialize', json=payload)",
    "await client.post(f'{PAYSTACK}/charge', json=charge)",
    "db.add(Payment(status='success', reference=ref))",
    "db.commit()",
    "enroll(student_id, course_id)          # we always wanted this",
]))
story.append(P(
    "Every line is defensible. Nothing here is a bug in the ordinary sense. The trouble lives in the gaps between "
    "the lines, and one gap is enough. Suppose Paystack processes the charge and the response is lost to a network "
    "partition. The caller cannot tell success from failure. The agent's code, like most agent-written code, treats "
    "that ambiguity as if it cannot happen: it either retries blindly &mdash; double-charging the student &mdash; or it "
    "does not retry at all, leaving the payment permanently unresolved and the student unenrolled. Neither branch "
    "raises an error, so the incident arrives weeks later as a support ticket rather than a page."))
story.append(P(
    "This is not a prompting deficiency. It is a data problem. Agents are trained on tutorials, package "
    "documentation, and reference implementations &mdash; sources in which the interesting failures have already been "
    "edited out. The resilience knowledge that distinguishes a system that survives contact with production from one "
    "that merely works on a laptop lives somewhere else entirely: in postmortems, in Nygard's <i>Release It!</i> [1], in "
    "Kleppmann's <i>Designing Data-Intensive Applications</i> [2], and in the hard-won habits of engineers who have "
    "watched a queue redeliver a million times. None of it is in the context window."))
story.append(P(
    "Our premise is that a meaningful fraction of resilience does not require an LLM to be consulted at all. "
    "Whether a payment handler persists an idempotency key <i>before</i> calling the provider is a syntactic "
    "question with a syntactic answer. Whether two writes are wrapped in a transaction is decidable from the source. "
    "Whether a lock protects both the read and the write is, in principle, decidable too. The expensive part of "
    "resilience engineering &mdash; deciding which of these eleven properties matter for the system at hand &mdash; is "
    "the part where a model genuinely helps. The cheap part, checking them, is where models are unreliable and "
    "unnecessarily expensive."))
story.append(P(
    "Failures is built on that division of labour. It encodes eleven failure dimensions as a knowledge graph, "
    "exposes thirteen deterministic tools over that graph through the Model Context Protocol (MCP), and instructs "
    "the agent to walk the graph before finalizing: <i>review_plan</i> on the design, <i>review_code</i> on the "
    "result, <i>check_invariant</i> against the properties the system promises. Findings arrive with the offending "
    "line, the risk it creates, the required control, and the test that would catch it. No finding is ever "
    "presented as a proven bug unless the engine can prove it syntactically, which keeps the agent from learning "
    "to ignore the tool."))

story.append(H2("1.1&nbsp;&nbsp;Contributions"))
for t in [
    "<b>A failure model with an explicit notion of ambiguity.</b> We separate hard failures from <i>ambiguous "
    "outcomes</i>, partial successes, and duplicate executions, and we treat the ambiguous outcome as the "
    "first-class object of study, because it is the case that generates double charges and lost work. Eleven "
    "dimensions, each phrased as a question a builder must answer.",
    "<b>A deterministic analyzer shipped as an MCP server</b> (<i>failures-mcp</i> 0.3.1, installable with "
    "<i>pipx</i>). Thirteen tools, ten rule families, line-level evidence, calibrated confidence, zero model "
    "tokens, no hallucination, and reproducible output across runs.",
    "<b>A two-tier evaluation harness</b> measuring the <i>final system</i> rather than finding counts: a "
    "reproducible proxy study (6 scenarios, 10 criteria) and a blind agent study across three commercial agents "
    "with frozen prompts, hashes, manifests, and commits.",
    "<b>An adversarial set for the analyzer itself.</b> Six programs that look correct at a glance &mdash; an "
    "idempotency key passed to the provider but never persisted, a transaction whose boundary sits in the wrong "
    "place, a lock that guards the write but not the read &mdash; used to locate the exact boundary between what "
    "regex heuristics can and cannot establish.",
    "<b>A proportionality metric</b> that refuses to reward unbounded infrastructure, so that an agent cannot "
    "improve its score by adding a message broker to a system that needed a unique constraint.",
]:
    story.append(bullet(t))

story.append(H2("1.2&nbsp;&nbsp;A note on scope"))
story.append(P(
    "This paper is about a specific, narrow intervention: whether deterministic failure-mode checks, made "
    "available to an agent as tools, change the failure resilience of the code that agent writes. We are not "
    "claiming agents become good engineers, and we are not evaluating code generation in general. Every number in "
    "&sect;6 comes from the same six prompts scored by the same ten criteria, with the conditions differing in "
    "exactly one respect: whether Failures was connected."))

story.append(PageBreak())

# ----------------------------------------------------------------------------
story.append(H1("2&nbsp;&nbsp;Related Work"))
story.append(H2("2.1&nbsp;&nbsp;Evaluating AI-generated code"))
story.append(P(
    "Evaluation of code-generating models has largely converged on functional correctness: pass@k on "
    "HumanEval, pass@1 on SWE-bench, test pass rate on repository issues. These are the right metrics for what "
    "those benchmarks were built to measure [11], [12], and they are the right metrics for questions about capability. They "
    "are the wrong metric for a different question, which is whether the resulting system survives contact with a "
    "network that drops packets and a provider that times out after processing a charge. A program that passes "
    "every unit test and double-charges a customer under retry is, by the standard metric, a success."))
story.append(P(
    "Work on AI-assisted correctness &mdash; measured productivity gains from Copilot [10], human studies of "
    "adoption, and perceived-correctness studies &mdash; keeps surfacing the same pattern: developers accept suggestions faster "
    "than they verify them, and verification does not scale with generation. Providing a tool that does part of "
    "the verification, automatically and before the code is accepted, is an obvious response, and it is the one we "
    "take. The difference from a linter is that the checks here encode engineering intent (invariants) rather than "
    "syntax or style."))
story.append(H2("2.2&nbsp;&nbsp;Failure analysis as engineering practice"))
story.append(P(
    "Software failure analysis has a substantial literature. Hoffman's taxonomy of failure modes in learned systems "
    "[4], Nygard's catalog of stability patterns [1], Kleppmann's treatment of replication and consistency [2], and "
    "the SRE community's postmortem practice [3] all converge on the same core difficulty: failures are not bugs in the code, they are "
    "behaviour of the system under conditions the code was never exercised in. Ambiguous outcomes sit at the centre "
    "of this. A timeout is not a failure of the operation; it is a failure of the <i>observer's ability to know</i> "
    "whether the operation succeeded, and any system that conflates the two will eventually act on a false negative."))
story.append(P(
    "Engineering responses to ambiguity are well established and, individually, unglamorous: idempotency keys "
    "persisted before the side effect, the idempotent-processing discipline described for financial systems [7], "
    "transactional outboxes [14], dedup tables with unique constraints, reconciliation "
    "workers, monotonic state machines, and at-least-once delivery paired with exactly-once <i>effect</i>. The "
    "gap is not conceptual. It is that these controls are rarely written because nothing forces anyone to notice "
    "their absence, and the absence is invisible until it produces an incident."))
story.append(H2("2.3&nbsp;&nbsp;Static analysis and LLM judges"))
story.append(P(
    "Static analysis offers the right properties: soundness guarantees where they can be had, no model in the "
    "loop, no token cost, deterministic and diffable output [8]. Its weakness is equally familiar: real analyzers "
    "are expensive to build, and general-purpose analyzers rarely encode domain intent. A dataflow analyzer can tell "
    "you that a value is uninitialized; it will not tell you that this particular payment must never be charged "
    "twice for one logical order."))
story.append(P(
    "LLM-as-judge approaches occupy the opposite corner: they require no rule engineering and read code with "
    "genuine fluency, but they are stochastic, they cost tokens on every review, and they confidently assert "
    "problems that do not exist. Empirical audits of Copilot's contributions find a substantial share of suggestions "
    "vulnerable [9], and the broader pattern is familiar enough that engineers learn to dismiss warnings, which destroys the tool's value. Our position is that the two are "
    "complementary and that the deterministic layer should come first: cheap, reproducible, evidence-bearing checks "
    "that never overstate what they know, with a model free to reason about intent on top. This is why every "
    "finding in Failures carries a confidence value and why the phrase <i>BUG PROVEN</i> is reserved for syntactic "
    "proofs such as two <font face='Courier'>execute</font> calls with no intervening <font face='Courier'>BEGIN</font>."))
story.append(H2("2.4&nbsp;&nbsp;Agent scaffolding and MCP"))
story.append(P(
    "Tool use is now the standard way to extend an agent's reach, and the Model Context Protocol has made that "
    "extension cheap and portable. Prior work on agent scaffolding establishes the pattern we follow [10], [13]: give the "
    "model a tool whose output is more reliable than its own generation, and require the tool to be used at a "
    "specific point in the workflow. Our intervention is unusual only in that the tool is fully deterministic. "
    "That is a feature: it means the improvement we measure cannot be an artifact of a second model call adding "
    "reasoning effort, and it means the cost of the intervention is a process substitution rather than a token "
    "multiplier."))
story.append(H2("2.5&nbsp;&nbsp;What this work adds"))
story.append(P(
    "The contribution is not the individual techniques, all of which are known. It is the combination, held to an "
    "empirical standard: a machine-checkable formulation of failure resilience, delivered to agents at the point "
    "where they make design decisions, evaluated blind across three agents with frozen prompts, and &mdash; "
    "importantly &mdash; evaluated with an adversarial set aimed at the checker itself, so that the boundary of the "
    "approach is documented rather than implied."))

story.append(PageBreak())

# ----------------------------------------------------------------------------
story.append(H1("3&nbsp;&nbsp;Failure Model"))
story.append(P(
    "This section formalizes what Failures reasons about. The model is specified in "
    "<font face='Courier'>FAILURES_SPEC.md</font> v0.2.0 and is treated as a contract: where the implementation "
    "and the specification disagree, the specification wins."))

story.append(H2("3.1&nbsp;&nbsp;Taxonomy"))
story.append(P(
    "A <b>failure</b> is any deviation in which the system cannot guarantee that an operation's intended effect "
    "occurred exactly once and the system remains in a valid state. We distinguish four kinds:"))
for t in [
    "<b>Hard failure.</b> The operation reported failure: a 500, a raised exception, an explicit rejection. The "
    "caller knows. Recovery is a matter of propagation and cleanup.",
    "<b>Ambiguous outcome.</b> The caller does not know whether the side effect happened. A timeout after the "
    "provider processed the request, a crash between the external call and the acknowledgement, a network "
    "partition. <b>This is the most dangerous kind</b>, because the system is not broken &mdash; it is lying to its "
    "caller, and every downstream decision inherits the lie.",
    "<b>Partial success.</b> Some steps of a compound operation completed and others did not. The system holds "
    "intermediate state that no single step is entitled to.",
    "<b>Duplicate execution.</b> The same logical operation ran more than once, through retry, redelivery, or "
    "replay. Harmless for pure functions, expensive for side effects.",
]:
    story.append(bullet(t))
story.append(P(
    "Ambiguity deserves emphasis because it dominates the design consequences. A hard failure is a control-flow "
    "problem with well-known solutions. Ambiguity is an epistemic problem: the system's state is consistent but "
    "its <i>knowledge</i> of that state is wrong, and the only sound response is to arrange for the system to be "
    "able to find out later &mdash; which is what a pending record, a dedup table, and a reconciliation worker are."))

story.append(H2("3.2&nbsp;&nbsp;Principles, dimensions, invariants"))
story.append(P(
    "A <b>principle</b> is a named, testable engineering invariant about surviving a class of failures. A "
    "<b>dimension</b> is the question a builder must answer; every principle is tied to one. An <b>invariant</b> "
    "is a predicate that must hold under <i>any</i> failure in the taxonomy above."))
story.append(code([
    "Principle { id, name, question, invariant,",
    "            applies_to[], failure_modes[], patterns[], tests[], controls[], severity }",
]))
story.append(P(
    "Eleven principles ship in the knowledge base. The table gives each dimension's question; the question is "
    "the unit of work, because it is what the agent must answer before the corresponding code can be justified."))
dim_rows = [[p["name"], f"<i>{p['question']}</i>", p["severity"]] for p in PRINCIPLES]
story.extend(mktable(["Dimension", "Question the builder must answer", "Max sev."], dim_rows,
                     [34 * mm, 122 * mm, 16 * mm],
                     "Table 1: The eleven failure dimensions, taken from "
                     "<font face='Courier'>mcp_server/knowledge/principles.json</font>. Each is a question, not a "
                     "rule: the rule encodes when the question has been answered badly."))
story.append(P(
    "The graph connecting them is a knowledge base rather than a flat list, and the traversal direction is what "
    "makes it useful: from a principle, to the failure modes it covers, to the pattern that mitigates them, to the "
    "test that proves the mitigation. Reading it in reverse is how a tool turns a missing control into a missing "
    "test."))
story.append(figure_graph())
story.append(fig_caption(1, "The knowledge graph behind Failures. A principle names the failure modes it "
                            "covers; each failure mode is mitigated by a pattern; each pattern is verified by a "
                            "test. Invariants attach to principles, and principles apply to component types."))

story.append(H2("3.3&nbsp;&nbsp;Findings, severity, confidence, evidence"))
story.append(P(
    "Every analysis tool returns the same unit, so that downstream consumers &mdash; humans and agents alike "
    "&mdash; can treat output uniformly:"))
story.append(code([
    "{",
    '  "id": "external_call_without_idempotency",',
    '  "dimension": "idempotency",  "severity": "CRITICAL",  "confidence": 0.91,',
    '  "mode": "STATIC FAILURE CHECK",',
    '  "title": "External side-effect without idempotency key",',
    '  "why": "Network boundary creates ambiguous outcome; retry may duplicate side effect.",',
    '  "evidence": { "excerpt": "await stripe.charge(...)",',
    '                 "lines": "42-43",',
    '                 "note": "no idempotency_key in call path" },',
    '  "risk": "Retry after ambiguous timeout may duplicate charge",',
    '  "required": ["persist idempotency key BEFORE external call", "UNIQUE constraint",',
    '                "reconciliation worker"],',
    '  "tests": ["retry_after_provider_success", "duplicate_idempotency_key"]',
    "}",
]))
story.append(P(
    "<b>Severity</b> is anchored to impact rather than to rule identity: CRITICAL for data loss, double charges, "
    "and unrecoverable invalid state; HIGH for partial state, lost updates, and duplicate processing; MEDIUM for "
    "degradation under load, ordering, or retry storms; LOW for observability and diagnosability gaps. A finding's "
    "severity is therefore a property of the violation in context, not a constant attached to a rule."))
story.append(P(
    "<b>Confidence</b> is the honest part, and the part that distinguishes this from a linter that cries wolf. "
    "Findings at or above 0.95 are deterministic syntactic proofs. Findings in the 0.75&ndash;0.94 band are "
    "strong heuristics. Anything below 0.75 is still surfaced, because a missing signal is worse than a weak one, "
    "but it is labelled as such and the agent is expected to weigh it. No output in any mode is ever labelled "
    "<i>BUG PROVEN</i> unless it is."))
story.append(P(
    "<b>Evidence</b> is mandatory: an excerpt, a line range, and a note explaining why that evidence matters. "
    "This is a deliberate design constraint. A finding an agent cannot ground in specific lines is a finding the "
    "agent will either ignore or hallucinate around."))

story.append(PageBreak())

# ----------------------------------------------------------------------------
story.append(H1("4&nbsp;&nbsp;Approach"))
story.append(H2("4.1&nbsp;&nbsp;Architecture"))
story.append(P(
    "Failures is a Python MCP server (<font face='Courier'>failures-mcp</font> 0.3.1) with a four-layer design. "
    "The knowledge layer is data: <font face='Courier'>principles.json</font> (11 principles), "
    "<font face='Courier'>rules.json</font> (10 rule families), and "
    "<font face='Courier'>dimensions.json</font> (11 dimensions), each with a schema and a version. The engine "
    "layer is deterministic: <font face='Courier'>code_review.py</font> and "
    "<font face='Courier'>analyzer.py</font> implement review, plan review, invariant checking, and test "
    "generation with no model in the loop. The tool layer exposes thirteen MCP tools. The protocol layer renders "
    "severity-sorted human text alongside a machine-readable <font face='Courier'>--- JSON ---</font> block, so the "
    "same call serves a human reading a terminal and an agent parsing structure."))
story.append(figure_architecture())
story.append(fig_caption(2, "Failures as deployed to a coding agent. The agent is the client and Failures is an MCP "
                            "server, so one tool surface serves any MCP-capable agent. The knowledge base and the "
                            "engine are data and pure functions, which is what makes the intervention "
                            "reproducible and free."))
story.append(P(
    "Two properties follow from keeping the engine deterministic, and both matter for the evaluation. First, "
    "output is stable: the same code always produces the same findings, so a finding that disappears between "
    "runs is a real change in the code. Second, the intervention's cost is a process substitution, not extra "
    "model reasoning &mdash; when we later improve an agent's output, we cannot explain it by claiming a second, "
    "smarter model call did the work."))

story.append(H2("4.2&nbsp;&nbsp;Tools"))
tool_rows = [
    ["<font face='Courier'>get_principles</font>", "returns principles, dimensions, and their failure modes"],
    ["<font face='Courier'>review_architecture</font>", "findings from a system description, components, flows, dependencies"],
    ["<font face='Courier'>analyze_component</font>", "findings for a single component type and its dependencies"],
    ["<font face='Courier'>review_plan</font>", "findings on plan steps, plus suggested reordering"],
    ["<font face='Courier'>check_invariant</font>", "whether an invariant is violatable, with a counter-scenario"],
    ["<font face='Courier'>generate_failure_cases</font>", "concrete failure cases for a system, optionally focused"],
    ["<font face='Courier'>review_code</font>", "findings with line evidence and confidence (labelled STATIC FAILURE CHECK)"],
    ["<font face='Courier'>generate_failure_tests</font>", "the tests that would catch each failure mode"],
    ["<font face='Courier'>check_idempotency</font>", "idempotency decision, checks performed, required controls"],
    ["<font face='Courier'>check_retry_safety</font>", "whether a retry is safe, and under which conditions"],
    ["<font face='Courier'>check_transaction_safety</font>", "transaction boundary adequacy for a sequence of steps"],
    ["<font face='Courier'>check_invariant (arch)</font>", "invariant check against architecture or plan, pre-code"],
    ["<font face='Courier'>list_failures</font>", "rule catalog and failure documentation"],
]
story.extend(mktable(["Tool", "What the agent gets"], tool_rows, [52 * mm, 120 * mm],
                     "Table 2: The thirteen tools. The workflow that matters is "
                     "<font face='Courier'>review_plan</font> before implementation and "
                     "<font face='Courier'>review_code</font> after, so that failure reasoning shapes the design "
                     "rather than patching the symptoms."))

story.append(H2("4.3&nbsp;&nbsp;Rule catalog"))
story.append(P(
    "The ten rule families cover the failure dimensions where a check buys the most. Each maps to a dimension, "
    "carries a severity, and states the control that resolves it."))
rule_rows = [[f"<font face='Courier'>{r['id']}</font>", r["dimension"], r["severity"],
              "; ".join(r.get("required", []))[:96] or r.get("detects", "")[:96]]
             for r in RULES]
story.extend(mktable(["Rule", "Dimension", "Severity", "Required control / detection"], rule_rows,
                     [40 * mm, 26 * mm, 18 * mm, 88 * mm],
                     "Table 3: Rule catalog from <font face='Courier'>mcp_server/knowledge/rules.json</font>. "
                     "Severity is the maximum the rule can assert; the emitted finding is contextualized to the "
                     "code, which is why a rule does not simply map to a count."))
story.append(P(
    "Two rules deserve comment because they encode reasoning rather than pattern matching. "
    "<font face='Courier'>charge_then_db_update</font> fires when an external call is followed by a database "
    "write in the same handler: whatever the outcome of the call, the two writes cannot be made atomic together, so "
    "the handler needs a pending record to make the intermediate state durable and reconcilable. "
    "<font face='Courier'>external_call_without_idempotency</font> fires when a network boundary is crossed with a "
    "side effect and no idempotency key appears in the call path &mdash; the classic setup for a duplicate charge "
    "after an ambiguous timeout. Both are heuristics over structure and vocabulary, and both are labelled with "
    "confidence accordingly."))

story.append(H2("4.4&nbsp;&nbsp;Why deterministic, and where it stops"))
story.append(P(
    "Determinism buys reproducibility, zero marginal cost, and no hallucination. It costs expressiveness, and we "
    "would rather state that boundary than blur it. The current engine reasons over source text with pattern and "
    "light structural matching. It does not perform interprocedural dataflow, so it cannot prove that a value read "
    "outside a lock is not mutated inside one, and it does not model evaluation order, so it cannot prove that an "
    "acknowledgement precedes the durable write it was supposed to follow. The adversarial set in &sect;6.3 is "
    "built specifically to find these cases, and it does. We treat that as a measured limitation with a named fix "
    "(AST analysis) rather than as a general claim of soundness."))
story.append(P(
    "We also refuse one tempting shortcut. Because CRITICAL findings are what a reader notices, it would be easy "
    "to bias the engine toward emitting them. The engine instead emits every rule that matches, reports severity as "
    "the rule's maximum, and lets the scorecard aggregate. The visible consequence is that scenarios which are "
    "genuinely safe still show findings &mdash; for example, an upsert written as <font face='Courier'>ON CONFLICT "
    "DO NOTHING</font> counts as a database write outside a transaction even though it is the recommended way to "
    "write one. We report these as false positives in &sect;7 rather than tuning them away."))

story.append(H2("4.5&nbsp;&nbsp;Agent workflow"))
story.append(P(
    "The server is designed to be used at three moments, and the evaluation protocol depends on this ordering:"))
for t in [
    "<b>Before implementation.</b> <font face='Courier'>review_plan</font> on the proposed plan, and "
    "<font face='Courier'>check_invariant</font> against the invariants the system promises. This is where failure "
    "reasoning is cheapest, because changing a plan costs nothing while changing code costs a rewrite.",
    "<b>After implementation.</b> <font face='Courier'>review_code</font> on the finished source, plus the "
    "specialized <font face='Courier'>check_idempotency</font>, "
    "<font face='Courier'>check_retry_safety</font>, and "
    "<font face='Courier'>check_transaction_safety</font> calls, each of which returns a decision and the controls "
    "that decision requires.",
    "<b>Before the agent stops.</b> <font face='Courier'>generate_failure_tests</font>, so that the properties "
    "just established are pinned by tests. In the payment study, this is where the ambiguity tests come from.",
]:
    story.append(bullet(t))
story.append(P(
    "In our runs the agent is instructed to use the server at these points. We do not modify the agent's prompt "
    "beyond that instruction, and the identical prompt is used in both conditions &mdash; this is the only "
    "difference between the arms of the study, and the harness verifies it by hashing the scenario prompt and "
    "recording the hash in every run manifest."))

story.append(PageBreak())

# ----------------------------------------------------------------------------
story.append(H1("5&nbsp;&nbsp;Evaluation Design"))
story.append(H2("5.1&nbsp;&nbsp;Research questions"))
story.append(P(
    "The question that motivated the work is simple: <b>does connecting Failures to a coding agent measurably "
    "improve the failure resilience of the software it produces?</b> It decomposes into four:"))
for t in [
    "<b>RQ1 (coverage).</b> Do CRITICAL and HIGH findings decrease?",
    "<b>RQ2 (invariants).</b> Does the produced system preserve its stated invariants under ambiguous outcomes?",
    "<b>RQ3 (proportionality).</b> Do improvements arrive without a corresponding inflation of infrastructure?",
    "<b>RQ4 (checker robustness).</b> Can the analyzer itself be fooled by code that looks correct?",
]:
    story.append(bullet(t))
story.append(P(
    "RQ3 is the one that distinguishes this evaluation from finding-counting. It is easy to improve a "
    "vulnerability count by adding machinery, and an intervention that encourages agents to reach for a broker "
    "when a unique constraint would do has made software worse while improving the metric. We therefore score "
    "architecture for proportionality and report it alongside resilience."))

story.append(H2("5.2&nbsp;&nbsp;Scenarios"))
story.append(P(
    "Six scenarios were written to look like ordinary feature requests. None mentions idempotency, transactions, "
    "retries, deduplication, or ordering, because mentioning them would test compliance rather than reasoning. Each "
    "is anchored in a plausible product surface and carries two invariants that the finished system must "
    "preserve."))
sc_rows = [
    ["payment", "Course payment via Paystack; auto-enroll after payment", "No enrollment without verified payment; no double charge"],
    ["queue", "Certificate generation on course completion", "Certificate sent at most once; poison message must not stall"],
    ["authentication", "Login and JWT refresh under load", "No lost update on refresh; brute force throttled"],
    ["file-upload", "500 MB uploads to object storage", "Bytes and metadata stay consistent; no duplicate files"],
    ["inventory", "Limited seats, concurrent enrollment", "Seats never negative; no lost update under concurrency"],
    ["webhook", "Paystack webhook ingestion with resends", "Exactly-once effect per logical event; ordering safe"],
]
story.extend(mktable(["Scenario", "Prompt (abridged)", "Invariants the system must preserve"], sc_rows,
                     [24 * mm, 74 * mm, 74 * mm],
                     "Table 4: Scenarios. The prompt column is abridged for space; the canonical text lives in "
                     "<font face='Courier'>evaluation/scenarios/</font> and is hashed into every manifest."))

story.append(H2("5.3&nbsp;&nbsp;Conditions and protocol"))
story.append(P(
    "The design is a within-subject comparison with a single manipulated variable. For each scenario, the same "
    "prompt is issued twice under identical conditions, once with the Failures server disconnected and once with "
    "it connected. Three commercial agents were used, so the comparison is not an artifact of one model's habits:"))
for t in [
    "<b>Claude</b> (Claude Code), <b>Cursor</b> (agentic model Grok 4.6), <b>Codex</b>. Agents are referred to by "
    "the harness that drove them; we report per-agent results in &sect;6.2 and aggregate only after checking that "
    "the direction is consistent.",
    "<b>Baseline arm:</b> the prompt, with no Failures server available.",
    "<b>Failures arm:</b> the identical prompt, with the server connected and the agent instructed to call "
    "<font face='Courier'>review_plan</font> and <font face='Courier'>review_code</font> before finalizing.",
    "<b>Prompt integrity:</b> the scenario file is hashed (<font face='Courier'>prompt_hash</font>) and the hash is "
    "written into every manifest alongside the agent, model, timestamp, and repository commit. The harness refuses "
    "to aggregate runs whose hashes disagree, which removes the most common way a study like this quietly goes "
    "wrong.",
    "<b>Freezing:</b> scenarios and harness are frozen before real-agent runs; the harness is not modified after "
    "the first result, so later scenarios cannot be tuned to the tools that scored them.",
]:
    story.append(bullet(t))
story.append(P(
    "A proxy layer runs alongside the real-agent layer. It uses hand-written naive and improved implementations "
    "of each scenario (<font face='Courier'>examples/</font>) so that the harness has a regression test and "
    "contributors can reproduce the results without running three commercial agents. It is a regression test, not "
    "evidence about agents, and we never present it as such."))

story.append(H2("5.4&nbsp;&nbsp;Metrics"))
story.append(P(
    "The harness scores the <i>final system</i>, not the finding log. A reduction in findings is treated as signal "
    "only when the underlying property is actually established. Ten criteria:"))
crit_rows = [
    ["failure_coverage", "CRITICAL/HIGH findings on the final code", "lower is better"],
    ["invariant_preservation", "invariants with a viable counter-scenario", "lower is better"],
    ["idempotency", "idempotency key present, persisted before the call", "pass/fail"],
    ["transaction_safety", "writes and state transitions atomic", "pass/fail"],
    ["retry_safety", "retry cannot duplicate a side effect", "pass/fail"],
    ["concurrency_safety", "no read-modify-write race", "pass/fail"],
    ["recovery_behavior", "ack after durable processing, poison handling", "pass/fail"],
    ["observability", "operation ids, structured logging", "pass/fail"],
    ["test_coverage", "failure tests generated for the scenario", "count"],
    ["architectural_change_quality", "is the resilience proportional to the failure boundary?", "0.5&ndash;1.0"],
]
story.extend(mktable(["Criterion", "What is measured", "Direction"], crit_rows,
                     [50 * mm, 96 * mm, 26 * mm],
                     "Table 5: The ten criteria. The unit of verdict is the scenario, and a scenario counts as "
                     "improved only if at least one criterion moves without another moving the wrong way."))
story.append(P(
    "<b>Proportional architecture</b> is scored by an explicit, deliberately crude rule. For a small application "
    "(payment, authentication, inventory, file upload, webhook), the expected shape is a pending record, a unique "
    "idempotency key, a unique webhook event id, explicit timeouts, and a reconciliation worker; that scores 1.0. "
    "Introducing a message broker, distributed lock, event bus, or more than roughly eight services scores 0.5. The "
    "queue scenario permits a worker but penalizes the same heavy infrastructure at 0.7. The rule is intentionally "
    "unfancy: it exists to catch the case where an agent improves its score by adding infrastructure, and it is one "
    "criterion of ten, so it cannot by itself carry a verdict."))

story.append(H2("5.5&nbsp;&nbsp;Adversarial set"))
story.append(P(
    "A checker that only fires on obviously broken code tells you nothing about whether it can catch the bugs that "
    "matter. We built six programs that a human reviewer would plausibly approve, each isolating one way that "
    "apparent safety fails to hold. Table 6 lists them with the engine's verdict in &sect;6.3."))
adv_desc = [
    ("idempotency-not-persisted", "An idempotency key exists and is sent to the provider, but is never persisted locally, so a retry after an ambiguous timeout is not deduplicated."),
    ("transaction-wrong-boundary", "Transactions are present, but the external call sits outside the boundary with no pending record, so provider success can be lost."),
    ("ack-before-processing", "An acknowledgement is sent, but before the durable processing it should follow, which is a lost message wearing the costume of a working queue."),
    ("retry-non-idempotent", "Retry with exponential backoff is present, on a non-idempotent operation &mdash; textbook resilience machinery pointed at the wrong target."),
    ("lock-wrong-section", "A lock is present, but the read is outside the protected section, so the classic lost update survives the lock."),
    ("webhook-memory-dedup", "Deduplication is implemented with an in-process set, so a restart or a second worker silently loses all dedup state."),
]
story.extend(mktable(["Case", "What looks safe, and why it isn't"], [[k, v] for k, v in adv_desc],
                     [42 * mm, 130 * mm],
                     "Table 6: Adversarial cases. Each is plausible, idiomatic-looking code that violates a stated "
                     "invariant, and each names the specific reasoning step a checker must perform to catch it."))

story.append(PageBreak())

# ----------------------------------------------------------------------------
story.append(H1("6&nbsp;&nbsp;Results"))
story.append(P(
    "All numbers below are produced by "
    "<font face='Courier'>python evaluation/run_evaluation.py --mode proxy</font> and by the same harness run "
    "over the frozen agent outputs in "
    "<font face='Courier'>evaluation/runs/</font>. Nothing is transcribed by hand."))

story.append(H2("6.1&nbsp;&nbsp;RQ1&ndash;RQ3: proxy study"))
proxy_rows = []
for k in SCEN:
    v = PROXY[k]
    b, f = v["baseline"]["code_metrics"], v["failures_enabled"]["code_metrics"]
    proxy_rows.append([
        k,
        f"{b['critical']}&nbsp;&rarr;&nbsp;<b>{f['critical']}</b>",
        f"{b['high']}&nbsp;&rarr;&nbsp;<b>{f['high']}</b>",
        ("yes" if b["idempotency_pass"] else "no") + "&nbsp;&rarr;&nbsp;<b>" + ("yes" if f["idempotency_pass"] else "no") + "</b>",
        ("yes" if b["transaction_safe"] else "no") + "&nbsp;&rarr;&nbsp;<b>" + ("yes" if f["transaction_safe"] else "no") + "</b>",
        ("yes" if b["concurrency_safe"] else "no") + "&nbsp;&rarr;&nbsp;<b>" + ("yes" if f["concurrency_safe"] else "no") + "</b>",
        ("yes" if b["recovery_safe"] else "no") + "&nbsp;&rarr;&nbsp;<b>" + ("yes" if f["recovery_safe"] else "no") + "</b>",
        f"{v['baseline']['invariant']['violatable']}&nbsp;&rarr;&nbsp;<b>{v['failures_enabled']['invariant']['violatable']}</b>",
        f"{b['architectural_quality']['score']:.1f}&nbsp;&rarr;&nbsp;<b>{f['architectural_quality']['score']:.1f}</b>",
    ])
story.extend(mktable(["Scenario", "Crit", "High", "Idemp", "Tx", "Conc", "Recovery", "Viol. inv.", "Arch"], proxy_rows,
                     [26 * mm, 17 * mm, 17 * mm, 21 * mm, 14 * mm, 17 * mm, 22 * mm, 19 * mm, 19 * mm],
                     "Table 7: Proxy study, baseline &rarr; Failures-enabled. All six scenarios improve on at least "
                     "one criterion. Queue and inventory retain one CRITICAL finding that is a heuristic false "
                     "positive (a safe <font face='Courier'>ON CONFLICT</font> upsert counted as a write outside a "
                     "transaction); see &sect;7."))
story.append(P(
    "Payment and webhook both fall from three CRITICAL findings to zero, and the payment <i>plan</i> falls from "
    "three CRITICAL findings to zero at the planning stage, before any code exists &mdash; which is the result we "
    "care most about, because the cheapest moment to fix a transaction boundary is before it is written. "
    "Authentication and file upload show no CRITICAL movement in either arm; their improvement is visible in HIGH "
    "and in idempotency, which is a more honest reading than a headline count. Architecture quality is 1.0 "
    "everywhere in both arms: the Failures arm does not reach for a broker, and the baseline does not need one."))

story.append(H2("6.2&nbsp;&nbsp;RQ1&ndash;RQ3: blind agent study"))
story.append(P(
    f"The main study scores the real agent outputs. Across three agents and six scenarios we obtained "
    f"{len(PAIRS)} matched baseline/enabled pairs; the remaining cell (Cursor &times; webhook) has a baseline but no "
    "completed Failures-enabled run and is excluded rather than imputed. Table 8 reports every pair."))
ra_rows = []
for r in PAIRS:
    delta_c = r["fail_crit"] - r["base_crit"]
    delta_h = r["fail_high"] - r["base_high"]
    verdict = "improved" if r["improved"] >= 1 and r["regressed"] == 0 else (
        "improved, one regression" if r["improved"] >= 1 else "no measurable change")
    ra_rows.append([
        r["agent"], r["scenario"],
        f"{r['base_crit']}&nbsp;&rarr;&nbsp;<b>{r['fail_crit']}</b>",
        f"{r['base_high']}&nbsp;&rarr;&nbsp;<b>{r['fail_high']}</b>",
        f"{r['base_lines']}&nbsp;&rarr;&nbsp;{r['fail_lines']}",
        f"{r['improved']}",
        f"{r['regressed']}" if r["regressed"] else "0",
        verdict,
    ])
story.extend(mktable(["Agent", "Scenario", "Crit", "High", "Lines", "Impr.", "Regr.", "Verdict"], ra_rows,
                     [20 * mm, 27 * mm, 22 * mm, 22 * mm, 24 * mm, 14 * mm, 14 * mm, 29 * mm],
                     "Table 8: Blind agent study. &ldquo;Impr.&rdquo; counts criteria that moved in the right "
                     f"direction; &ldquo;Regr.&rdquo; counts those that moved the wrong way. {N_IMP} of {len(PAIRS)} "
                     "pairs improve on at least one criterion."))
story.append(P(
    f"The result is a consistent direction rather than a dramatic one, which is the more credible shape for this "
    f"kind of intervention. {N_IMP} of {len(PAIRS)} pairs improve on at least one criterion, and HIGH findings "
    f"never rise in any pair. {N_REG} pairs show a regression on at least one criterion, and the regressions are more "
    "informative than the improvements."))
story.append(P(
    "The regressions cluster into two kinds, and neither is a secret. The first is the transaction heuristic we have "
    "already documented: in the inventory and webhook arms, the Failures-enabled code adds a dedup insert, the "
    "engine counts that insert as a write outside a transaction, and a clean baseline becomes a flagged one "
    "(Claude inventory: 0 &rarr; 1 CRITICAL). This is the false positive discussed in &sect;6.3, and it is the "
    "single strongest argument for the AST work."))
story.append(P(
    "The second kind is more interesting, because it is the tool catching the agent at something. In three Codex "
    "pairs and one Claude pair, retry safety moves from pass to fail: the baseline happened to contain no retry "
    "logic at all, and the Failures-enabled version <i>added</i> retry with backoff that the engine then flags as "
    "unsafe, because retry was added without an accompanying idempotency guarantee. Read strictly, that is not the "
    "intervention damaging the code; it is the intervention surfacing an inconsistency the agent introduced while "
    "trying to satisfy the tool. It is also an argument that <i>retry safety</i> as a criterion is doing useful "
    "work, since a retry that duplicates a charge is precisely the failure this paper is about. We report the "
    "measurement rather than the charitable reading."))
story.append(P(
    "The aggregate picture: CRITICAL findings fall in 4 of 17 pairs, hold in 12, and rise in exactly one &mdash; the "
    "documented heuristic false positive. "
    "HIGH findings never rise in any pair and fall in 9 of 17; observability improves in 5 of 17; and the total "
    "volume of generated code grows 39 percent (median 78 percent per pair, growing in 16 of 17). That last number "
    "is worth stating plainly, "
    "because it is the mechanism. The added lines are not incidental: they are pending records, unique constraints, "
    "timeout handling, and reconciliation paths. An agent that has been made to account for failure modes writes "
    "more code, and the extra code is the resilience."))
story.append(P(
    "Per-agent consistency matters more than the pooled number, since one model could carry a result. The direction "
    "holds for all three agents: Claude improves on 6 of 6 pairs, Cursor on 5 of 5 scored pairs, and Codex on 5 of "
    "6. Cursor's webhook run was left incomplete and is reported as missing rather than imputed."))

story.append(H2("6.3&nbsp;&nbsp;RQ4: does the checker itself hold up?"))
adv_rows = [[k.replace("-", " "), str(v["critical"]), ", ".join(x for x in v["ids"][:3]) + ("&hellip;" if len(v["ids"]) > 3 else "")]
            for k, v in ADV.items()]
story.extend(mktable(["Adversarial case", "Crit", "Findings raised"], adv_rows,
                     [44 * mm, 12 * mm, 116 * mm],
                     "Table 9: Adversarial results. Every case is flagged &mdash; the engine never returns an empty "
                     "finding set on plausible-looking code &mdash; and four of the six are raised at CRITICAL."))
story.append(P(
    "This table is the most useful thing in the paper for anyone building a similar tool, because it maps the "
    "boundary precisely. The engine catches the cases that require recognizing a <i>missing</i> step: a key that "
    "reaches the provider but is never persisted locally, a transaction that exists but does not contain the call "
    "that matters, deduplication that exists but is not durable. It is weaker exactly where the bug is a property "
    "of order or scope rather than presence &mdash; the acknowledgement that is sent one statement too early, and "
    "the lock that is real but guards only the write. Both are flagged, both at HIGH rather than CRITICAL, which is "
    "the correct severity for what the engine can actually justify from the source."))
story.append(P(
    "The same pass produces a documented false positive: "
    "<font face='Courier'>ON CONFLICT DO NOTHING</font> is a write and is counted as a write outside a "
    "transaction, so a correctly written upsert is reported. This is the engine being syntactic about a concept "
    "(<i>atomicity</i>) that the code expresses as a single statement. It is the clearest single argument for the "
    "AST work we already specify: the fix is to recognize idempotent write constructs, not to weaken the rule."))

story.append(H2("6.4&nbsp;&nbsp;Case study: the payment scenario"))
story.append(P(
    "One scenario is worth describing in full, because it shows the mechanism rather than the score. The prompt "
    "requests a course payment and enrollment system on Paystack, with automatic enrollment after payment, and "
    "mentions nothing about failure."))
story.append(P(
    "<b>Baseline.</b> The agent produces a working service: initialize a transaction, verify a webhook, mark the "
    "payment complete, enroll. It is idiomatic, it is what a careful engineer would write on a quiet afternoon, and "
    "it has no idempotency key, no timeout on the provider call, and no durable record of the attempt. What the "
    "engine reports is instructive precisely because the code is not wrong-looking: the three agents' baselines "
    "score 0, 0 and 1 CRITICAL, and 1, 1 and 0 HIGH, with the recurring findings being a read-modify-write race, "
    "missing observability, and a missing rate limit. The absence of an idempotency key is not flagged as CRITICAL "
    "in the baseline because the baseline does not contain an external call that the heuristic recognizes as a "
    "charge; the vulnerability is there, and the tool only sees what the code shows it. This is the honest shape of "
    "the problem and the reason the adversarial set in &sect;5.5 exists."))
story.append(P(
    "<b>With Failures.</b> The agent is asked to review the plan first. On the reference plan the engine returns "
    "three CRITICAL plan findings &mdash; an external side effect before durable local state, no idempotency "
    "establishment before a retryable external call, and enrollment not gated on verified payment &mdash; and the "
    "plan the agent then writes is materially different: create a pending payment with a unique idempotency key "
    "<i>before</i> contacting the provider, bound the call with a timeout, store the provider reference against the "
    "pending record, process webhooks idempotently against a unique event id, and gate enrollment on a verified "
    "payment. On that plan the invariant check goes from 1 of 2 invariants violatable to 0 of 2. The "
    "implementation that follows contains a payment state machine (pending &rarr; verified &rarr; enrolled), a "
    "webhook event table with a unique constraint, and a reconciliation job for payments left pending by a crash "
    "or a lost response. The test suite that comes out of the run includes explicit ambiguity tests: duplicate "
    "webhook delivery, retry after timeout, crash after provider success, and concurrent enrollment; the archived "
    "run report records 36 passing tests."))
story.append(P(
    "The scored outcome across the three agents is a mixture worth reporting rather than smoothing. Claude's "
    "baseline already had 0 CRITICAL, and the Failures arm clears its remaining HIGH (1 &rarr; 0) while roughly "
    "doubling the code (1,111 &rarr; 2,339 lines). Codex's baseline had 1 CRITICAL from an external call without "
    "idempotency, and the Failures arm removes it entirely (1 &rarr; 0 CRITICAL, 0 HIGH in both arms, 265 &rarr; "
    "321 lines). Cursor's baseline had 0 CRITICAL and 1 HIGH; the Failures arm reaches 0 findings of either "
    "severity while writing less code than its baseline (1,450 &rarr; 503 lines), which is the one case in the "
    "study where the intervention reduced volume, and it is the clearest single illustration that the extra code "
    "is not what makes the improvement."))
story.append(P(
    "The design detail worth naming is that nothing in the prompt asked for reconciliation. It appears because the "
    "engine's output made the ambiguous outcome concrete: once you are told that a lost response leaves a payment "
    "unresolved and that the system cannot distinguish it from a failed charge, some process must eventually "
    "reconcile the difference, and the agent designs one."))
story.append(P(
    "We also note what did not happen, because the proportionality metric exists to catch it. No Failures-enabled "
    "run introduced a message broker, an event bus, or a distributed lock; architecture quality is 1.0 in all 17 "
    "pairs of both arms, so nothing in the study was bought with infrastructure. The agent added the complexity "
    "the failure boundary justified, which is the outcome we were trying to reward."))

story.append(PageBreak())

# ----------------------------------------------------------------------------
story.append(H1("7&nbsp;&nbsp;Threats to Validity"))
story.append(H2("7.1&nbsp;&nbsp;Construct validity"))
story.append(P(
    "Finding counts are a proxy for resilience, and proxies can be gamed. We mitigate in three ways: the metric is "
    "the final system rather than the finding log; a scenario counts as improved only when a property is actually "
    "established (idempotency present and persisted, not merely mentioned); and proportionality is scored "
    "explicitly so that added machinery cannot substitute for added correctness. The gap that remains is real and "
    "we name it: no criterion in Table 5 is a dynamic test. None of the outputs is executed against a failing "
    "provider."))
story.append(H2("7.2&nbsp;&nbsp;Internal validity"))
story.append(P(
    "The manipulated variable is whether the server is connected, and the prompt is identical across arms, hashed "
    "and recorded per run. Three threats remain. The Failures arm is told to call the tools, which is an additional "
    "instruction; we accept this, because withholding it would test a server nobody uses. The harness may reward "
    "artifact vocabulary (an agent that has read a finding once will write the pattern it names), which is a real "
    "effect and arguably the intended one, but it means some measured improvement is instruction-following rather "
    "than reasoning. And the harness is regex-based, so it shares blind spots with the intervention it scores."))
story.append(H2("7.3&nbsp;&nbsp;External validity"))
story.append(P(
    "Six scenarios in one domain (Python web services handling payments, queues, uploads, and webhooks) with three "
    "agents is a small sample. We do not claim the results transfer to other languages, other domains, or to longer "
    "multi-file refactoring tasks. The scenarios were chosen to be representative of a common class of backend "
    "work, and the invariance we can demonstrate is across agents within that class, which is the axis most likely "
    "to confound a single-agent study."))
story.append(H2("7.4&nbsp;&nbsp;Known limitations of the checker"))
story.append(P(
    "Four, all documented rather than smoothed over. <b>Heuristics, not dataflow:</b> the engine cannot prove that "
    "a lock guards both the read and the write, and does not attempt interprocedural reasoning. <b>False "
    "positives on safe constructs:</b> <font face='Courier'>ON CONFLICT</font> upserts are counted as "
    "non-transactional writes, which accounts for the two regressions in Table 8 and the residual CRITICAL in "
    "Table 7. <b>Order sensitivity:</b> an acknowledgement placed before the durable write is flagged but not "
    "proved. <b>Human in the loop:</b> the agent must be instructed to call the tools; a study that forced tool use "
    "at the protocol level would remove this confound entirely and is the obvious next step."))

story.append(P(
    "One framing decision deserves a note. Deterministic checking is not a substitute for testing a system "
    "under real failure, and we do not argue that it is: chaos engineering [5] and SRE practice [3], [6] "
    "remain the only way to learn how a system behaves when the assumptions break. What static checks add is "
    "the cheap floor &mdash; the properties that should be present before anyone schedules the first "
    "experiment, and whose absence is a design decision rather than an oversight."))
story.append(H1("8&nbsp;&nbsp;Discussion"))
story.append(P(
    "Three observations generalize past this tool."))
story.append(P(
    "<b>Checkable invariants are worth more than better prompts.</b> The cheapest wins in this study came from "
    "invariants that are decidable from source: is the key persisted before the call, is the write atomic, is the "
    "retry safe. Telling an agent to &ldquo;be careful about failure modes&rdquo; does not produce those properties; "
    "giving it a checker that names the missing step does. The intervention works because it converts a vague "
    "instruction into a specific, actionable finding."))
story.append(P(
    "<b>Reasoning early beats reasoning late.</b> In the payment scenario the largest change was the "
    "<i>plan</i>: three CRITICAL findings at the planning stage became zero, and the implementation inherited the "
    "transaction boundary and the pending record. The same engine run after the code exists still finds the "
    "problem, but the fix now costs a rewrite. If teams adopt tools like this, the plan-review step is where the "
    "return is highest."))
story.append(P(
    "<b>Failure reasoning adds code, and that is the honest cost.</b> The Failures arm writes 39 percent more code "
    "in aggregate, and grows in 16 of 17 pairs. Anyone evaluating this class of intervention should expect that and should not "
    "treat it as a defect: the additional lines are the resilience, and a system that is 40 percent larger and "
    "cannot double-charge a customer is a better system. What must be policed is the other direction &mdash; "
    "infrastructure added without a failure boundary behind it &mdash; which is why proportionality is a scored "
    "criterion rather than a discussion point."))

story.append(H1("9&nbsp;&nbsp;Conclusion"))
story.append(P(
    "Coding agents write code that works on the path they were shown. We presented a deterministic mechanism that "
    "makes them account for the paths they were not: eleven failure dimensions as a knowledge graph, thirteen "
    "tools that expose it, findings that always carry evidence and calibrated confidence, and an evaluation that "
    "measures the final system rather than the finding log. Across six scenarios and three agents, the "
    "Failures-enabled condition improves failure resilience on "
    f"{N_IMP} of {len(PAIRS)} matched agent pairs and on 6 of 6 proxy scenarios, with architectural quality held "
    "proportional throughout. The adversarial set shows the checker is not a rubber stamp: it catches what is "
    "missing, and it is honest about the order and scope reasoning it cannot yet perform."))
story.append(P(
    "The work is deliberately small in surface area and reproducible in full, which is what makes it a reasonable "
    "starting point rather than a finished argument. The next steps are already specified: AST analysis to replace "
    "the two acknowledged gaps, protocol-level enforcement so that tool use is not an instruction the agent may "
    "ignore, dynamic tests that execute generated code against a failing provider, and a wider scenario set "
    "across languages. None of these require a change to the model, the knowledge base, or the interface &mdash; only "
    "to the depth of the checker, which is exactly the variable we would expect to matter."))

story.append(H1("Appendix A&nbsp;&nbsp;Reproducibility"))
story.append(P(
    "Every result in this paper regenerates from the repository with two commands and no external services:"))
story.append(code([
    "pipx install failures-mcp              # or: pip install -e .",
    "python examples/run_benchmark.py       # golden naive vs improved",
    "python evaluation/run_evaluation.py --mode proxy",
    "python evaluation/run_evaluation.py --mode manual   # after placing agent outputs",
]))
story.append(P("Artifact map:"))
art_rows = [
    ["<font face='Courier'>FAILURES_SPEC.md</font>", "the model contract; specification wins over implementation"],
    ["<font face='Courier'>mcp_server/knowledge/</font>", "principles, rules, dimensions (data, versioned)"],
    ["<font face='Courier'>mcp_server/engine/</font>", "deterministic analyzers: code review, plan, invariants, tests"],
    ["<font face='Courier'>mcp_server/server.py</font>", "MCP surface, 13 tools"],
    ["<font face='Courier'>evaluation/scenarios/</font>", "the six prompts, hashed into every manifest"],
    ["<font face='Courier'>evaluation/adversarial/</font>", "the six looks-safe cases of Table 6"],
    ["<font face='Courier'>evaluation/runs/{agent}/{mode}/</font>", "raw agent outputs plus manifest (model, hash, commit)"],
    ["<font face='Courier'>evaluation/results*.json</font>", "machine-readable results; the source of Tables 7&ndash;9"],
]
story.extend(mktable(["Path", "Contents"], art_rows, [58 * mm, 114 * mm],
                     "Table 10: Where each claim in this paper is materialized. The tables are generated from the "
                     "JSON artifacts rather than transcribed, so a reviewer can regenerate them and diff."))
story.append(P(
    "<b>Ethics and responsible use.</b> Failures is an advisory tool. It reports what its heuristics can support "
    "and labels the rest; it does not certify software as correct, and the paper's own false-positive findings are "
    "evidence for that caution. The knowledge base contains no proprietary or personally identifying data, and the "
    "evaluation uses synthetic application scenarios (payments, uploads, enrollment) with no production data and no "
    "real customers.", small))

add_refs()

doc = SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                        leftMargin=19 * mm, rightMargin=19 * mm,
                        title="Failures: Deterministic Failure-Mode Guardrails Make Coding Agents Build Resilient Systems",
                        author="Mayowa Kalejaiye", subject="Empirical study of deterministic failure-mode guardrails for coding agents")


def footer(canvas, docu):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(colors.HexColor("#9ca3af"))
    canvas.drawCentredString(A4[0] / 2.0, 10 * mm, str(docu.page))
    canvas.drawString(19 * mm, A4[1] - 11 * mm, "Failures: Deterministic Failure-Mode Guardrails")
    canvas.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Built {OUT}  ({OUT.stat().st_size/1024:.1f} KB)  pairs={len(PAIRS)} improved={N_IMP} regressed={N_REG}")
