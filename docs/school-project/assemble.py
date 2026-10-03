"""Final assembly of the Failures final-year project report.

Merges staged chapters, inserts auto-numbered front matter (TOC field,
Lists with PAGEREF fields, abbreviations, abstract), renders references in
first-cited order, and appends verified appendices. Open the result in Word
and press Ctrl+A then F9 to populate all fields.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docxcompose.composer import Composer

from common import OUT, REFS, STAGE_DIR, body, chapter_head, new_document, \
    page_break, para, section_head

SCHOOL = Path(__file__).resolve().parent
TMP_FIG = SCHOOL / "figures"
ROOT = SCHOOL.parent.parent


def field_run(paragraph, instr):
    r = paragraph.add_run()
    f1 = OxmlElement("w:fldChar")
    f1.set(qn("w:fldCharType"), "begin")
    r._r.append(f1)
    r2 = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    r2._r.append(it)
    r3 = paragraph.add_run()
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "separate")
    r3._r.append(f2)
    r4 = paragraph.add_run("…")
    r5 = paragraph.add_run()
    f3 = OxmlElement("w:fldChar")
    f3.set(qn("w:fldCharType"), "end")
    r5._r.append(f3)
    for run in (r, r2, r3, r4, r5):
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)


def add_bookmark(paragraph, name, bid):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bid))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bid))
    p = paragraph._p
    p.insert(0, start)
    p.append(end)


def list_entry(doc, text, bookmark):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.tab_stops.add_tab_stop(
        Inches(6.27), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r = p.add_run(text + "\t")
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    field_run(p, f"PAGEREF {bookmark} \\h")


TABLE_CAPTIONS = [
    "Table 2.1: Comparative Analysis of Reviewed Studies",
    "Table 3.1: Common System Development Methodologies",
    "Table 3.2: Functional Requirements",
    "Table 3.3: Non-Functional Requirements",
    "Table 3.4: Summary of Data Sources",
    "Table 3.5: Existing Workflow versus Proposed System",
    "Table 3.6: Implementation Tools",
    "Table 3.7: Test Cases and Results",
    "Table 4.1: Implementation Environment",
    "Table 4.2: Proxy Results by Scenario",
    "Table 4.3: Blind Agent Study by Agent",
    "Table 4.4: Adversarial Results",
    "Table 4.5: Mapping Objectives to Results",
]
FIGURE_CAPTIONS = [
    "Figure 3.1: System architecture of Failures.",
    "Figure 3.2: Knowledge graph \u2014 Principle \u2192 FailureMode \u2192 "
    "Pattern \u2192 Test.",
    "Figure 3.3: Use case diagram.",
    "Figure 3.4: Evaluation pipeline.",
    "Figure 4.1: Proxy findings per scenario, baseline versus enabled.",
    "Figure 4.2: Agent-study finding totals across all seventeen pairs.",
]

ABBREVIATIONS = [
    ("MCP", "Model Context Protocol"),
    ("DSR", "Design Science Research"),
    ("DSS", "Decision Support System"),
    ("LLM", "Large Language Model"),
    ("API", "Application Programming Interface"),
    ("JSON", "JavaScript Object Notation"),
    ("UAT", "User Acceptance Testing"),
    ("ERD", "Entity Relationship Diagram"),
    ("DFD", "Data Flow Diagram"),
    ("DOI", "Digital Object Identifier"),
    ("SEN", "Software Engineering"),
    ("PyPI", "Python Package Index"),
]

ABSTRACT = (
    "AI-assisted software development has made generated code a production "
    "input, while the benchmarks that judge it still measure functional "
    "correctness on exercised paths. This study addresses the resulting gap: "
    "the silent mishandling of failure modes, especially ambiguous outcomes "
    "in which a caller cannot tell whether a side effect occurred. Although "
    "resilience patterns are well catalogued and decision support systems "
    "exist for pattern selection, no deterministic, evidence-backed "
    "guardrail layer is delivered to coding agents as tools. The primary aim "
    "of this study was therefore to design, implement, and evaluate a "
    "deterministic failure-mode guardrail system for AI-generated software. "
    "Design Science Research guided the work and Agile organised the build "
    "of Failures, a thirteen-tool Model Context Protocol server over eleven "
    "failure dimensions, scored by a deterministic ten-criterion harness "
    "across six production-style scenarios. Seventeen matched "
    "baseline/enabled pairs from three commercial agents were compared, "
    "alongside a six-case proxy study and a six-case adversarial probe. The "
    "study found that sixteen of seventeen pairs improved on at least one "
    "criterion, HIGH findings never rose and fell from thirteen to one, and "
    "architecture quality held proportional throughout. These findings "
    "indicate that cheap, reproducible, evidence-backed checks measurably "
    "improve the failure resilience of agent-generated software. It is "
    "therefore concluded that deterministic guardrails provide a practical "
    "floor for resilience practice in agent-driven development, with "
    "heuristic limits honestly documented for future AST-level work."
)
KEYWORDS = ("AI-generated software; failure resilience; static analysis; "
            "Model Context Protocol; design science research")


def build_prelims():
    doc = new_document()
    chapter_head(doc, "TABLE OF CONTENTS")
    p = doc.add_paragraph()
    field_run(p, 'TOC \\o "1-2" \\h \\z \\u')
    page_break(doc)
    chapter_head(doc, "LIST OF TABLES")
    for i, cap in enumerate(TABLE_CAPTIONS):
        list_entry(doc, cap, f"TBL{i:02d}")
    page_break(doc)
    chapter_head(doc, "LIST OF FIGURES")
    for i, cap in enumerate(FIGURE_CAPTIONS):
        list_entry(doc, cap, f"FIG{i:02d}")
    page_break(doc)
    chapter_head(doc, "LIST OF ABBREVIATIONS")
    for abbr, meaning in ABBREVIATIONS:
        body(doc, f"{abbr} \u2013 {meaning}")
    page_break(doc)
    chapter_head(doc, "ABSTRACT")
    body(doc, ABSTRACT)
    kw = doc.add_paragraph()
    r = kw.add_run("Keywords: " + KEYWORDS)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    page_break(doc)
    path = STAGE_DIR / "stage_prelims.docx"
    doc.save(str(path))
    return path


TOOLS = [
    ("get_principles", "List Failures engineering principles and dimensions, "
     "optionally filtered by id."),
    ("review_architecture", "Review a system architecture for failure modes "
     "from a system description, components, flows, and dependencies."),
    ("analyze_component", "Analyze a single component type (database, queue, "
     "api, payment, auth, cache, worker, storage) for failure modes."),
    ("generate_failure_cases", "Generate concrete failure scenarios for a "
     "system, prioritising ambiguous and partial failures."),
    ("review_code", "Review source code for failure risks including "
     "idempotency, transactions, timeouts, race conditions, and retry "
     "safety, with evidence and confidence."),
    ("generate_failure_tests", "Generate failure-oriented tests for a "
     "system or component."),
    ("check_idempotency", "Check whether an operation or code fragment is "
     "safe to execute more than once."),
    ("check_retry_safety", "Determine whether retrying an operation can "
     "produce duplicate side effects or inconsistent state."),
    ("check_transaction_safety", "Analyse database and state transitions "
     "for partial commits, crashes, rollback behaviour, and lost updates."),
    ("review_plan", "Review an ordered implementation plan for failure "
     "ordering, idempotency, and transaction gaps before coding."),
    ("check_invariant", "Check whether declared invariants can be violated "
     "under failures, returning counter-scenarios."),
    ("review_code_semantic", "Semantic review combining deterministic checks "
     "with low-confidence heuristics for hard cases such as acknowledgement "
     "ordering and lock scope."),
    ("list_failures", "List known failure scenarios from the knowledge base."),
]


def scenario_texts():
    out = []
    for name in ["payment", "queue", "authentication", "file-upload",
                 "inventory", "webhook"]:
        text = (ROOT / "evaluation" / "scenarios" / f"{name}.md").read_text(
            encoding="utf-8")
        prompt = " ".join(
            ln.lstrip("> ").strip()
            for ln in text.splitlines() if ln.strip().startswith(">"))
        invs = [ln.strip()[2:].strip() for ln in text.splitlines()
                if re.match(r"\s*-\s*`I\d`", ln)]
        out.append((name, prompt, invs))
    return out


def build_back():
    doc = new_document()
    page_break(doc)
    chapter_head(doc, "REFERENCES")
    order = []
    for ch in ["stage_ch1", "stage_ch2", "stage_ch3", "stage_ch4",
               "stage_ch5"]:
        keys = json.loads((STAGE_DIR / f"{ch}.cited.json").read_text())
        order.extend(k for k in keys if k not in order)
    missing = [k for k in order if k not in REFS]
    assert not missing, missing
    import unicodedata

    def surname(k):
        first = REFS[k].split(",")[0]
        return "".join(
            c for c in unicodedata.normalize("NFKD", first)
            if not unicodedata.combining(c)).lower()

    for k in sorted(set(order), key=surname):
        body(doc, REFS[k])
    print(f"references: {len(set(order))}")
    page_break(doc)
    chapter_head(doc, "APPENDIX A: MCP TOOL CATALOGUE")
    body(doc, "The thirteen tools exposed by the Failures server "
              "(mcp_server/server.py), each verified against the running "
              "source:")
    for name, purpose in TOOLS:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(name + " \u2014 ")
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r2 = p.add_run(purpose)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(12)
    page_break(doc)
    chapter_head(doc, "APPENDIX B: EVALUATION SCENARIO PROMPTS")
    body(doc, "The six frozen scenario prompts, reproduced verbatim from "
              "evaluation/scenarios/. Each deliberately omits resilience "
              "terminology so that prompts test reasoning rather than "
              "compliance.")
    for name, prompt, invs in scenario_texts():
        section_head(doc, f"B.{['payment', 'queue', 'authentication', 'file-upload', 'inventory', 'webhook'].index(name) + 1} {name}")
        body(doc, f"Prompt: \u201c{prompt}\u201d")
        for inv in invs:
            it = doc.add_paragraph(style="List Bullet")
            run = it.add_run(inv)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
    path = STAGE_DIR / "stage_back.docx"
    doc.save(str(path))
    return path


def main():
    prelims = build_prelims()
    back = build_back()
    parts = [STAGE_DIR / "stage_front.docx", prelims,
             STAGE_DIR / "stage_ch1.docx", STAGE_DIR / "stage_ch2.docx",
             STAGE_DIR / "stage_ch3.docx", STAGE_DIR / "stage_ch4.docx",
             STAGE_DIR / "stage_ch5.docx", back]
    for p in parts:
        assert p.exists(), p
    composer = Composer(Document(str(parts[0])))
    for p in parts[1:]:
        composer.append(Document(str(p)))
    doc = composer.doc
    # bookmark Table/Figure captions for PAGEREF fields
    want = {}
    for i, cap in enumerate(TABLE_CAPTIONS):
        want[" ".join(cap.split())] = f"TBL{i:02d}"
    for i, cap in enumerate(FIGURE_CAPTIONS):
        want[" ".join(cap.split())] = f"FIG{i:02d}"
    bid, found = 1, []
    for para in doc.paragraphs:
        key = " ".join(para.text.split())
        if key in want:
            add_bookmark(para, want[key], bid)
            bid += 1
            found.append(want[key])
    print(f"bookmarked {len(found)}/{len(want)} captions")
    missing = set(want.values()) - set(found)
    if missing:
        print("MISSING captions:", sorted(missing))
    try:
        doc.save(str(OUT))
        print(f"Saved {OUT}")
    except PermissionError:
        alt = STAGE_DIR / "FAILURES_Final_Year_Project_Report_NEW.docx"
        doc.save(str(alt))
        print(f"OUT locked — saved instead to {alt}")


if __name__ == "__main__":
    from docx import Document
    from common import section_head
    main()
