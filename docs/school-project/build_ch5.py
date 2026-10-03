"""Chapter 5 of the Failures final-year project report. Stages to stage_ch5."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CITED, OUT, STAGE_DIR, body, chapter_head, cite, new_document,
                    page_break, section_head)

STAGE5 = STAGE_DIR / "stage_ch5.docx"
doc = new_document()
page_break(doc)
chapter_head(doc, "CHAPTER FIVE: SUMMARY, CONCLUSION AND RECOMMENDATIONS")

section_head(doc, "5.1 Summary of the Study")
body(doc, "This study investigated the failure resilience of AI-generated "
          "software. The study was motivated by the gap between what code "
          "generation benchmarks measure and what production punishes: "
          "correctness on exercised paths versus survival on unexercised "
          "ones. The overall aim of the study was to design, implement, and "
          "evaluate a deterministic failure-mode guardrail system, while "
          "the specific objectives were to investigate failure modes, design "
          "an invariant-based framework, develop it as a Model Context "
          "Protocol server, implement a deterministic evaluation harness, "
          "and evaluate the system through proxy and blind agent studies.")
body(doc, "To achieve these objectives, Design Science Research was adopted, "
          "with Agile development of the artefact and experimental scoring "
          "of matched baseline/enabled pairs. The proposed guardrail system "
          "was designed and implemented in Python as thirteen MCP tools over "
          "a versioned knowledge base of eleven principles and ten rule "
          "families, with a ten-criterion harness scoring six scenarios "
          "across three commercial agents.")
body(doc, "The results obtained showed that sixteen of seventeen agent pairs "
          "improved on at least one criterion, HIGH findings never rose and "
          "fell from thirteen to one, CRITICAL findings fell from nine to "
          "six, and architecture quality held proportional throughout. The "
          "study therefore demonstrates that deterministic, evidence-backed "
          "guardrails measurably improve the failure resilience of "
          "agent-generated software. Overall, the research successfully "
          "achieved its stated objectives and provides both a working tool "
          "and a reproducible evaluation method.")
cite(doc)

section_head(doc, "5.2 Conclusion")
body(doc, "Based on the findings of this study, it can be concluded that "
          "connecting deterministic failure-mode guardrails to a coding "
          "agent improves the failure resilience of what the agent produces, "
          "without trading correctness for infrastructure. The study "
          "successfully achieved its aim of designing, implementing, and "
          "evaluating the guardrail system through the five objectives, each "
          "mapped to evidence in Chapter Four.")
body(doc, "The findings demonstrate that the decisive intervention point is "
          "before code exists: plan-level review reshapes designs, while "
          "code-level review catches what remains. Consequently, the "
          "proposed guardrail server provides a cheap, reproducible floor "
          "for resilience practice and can serve as a pre-commit check in "
          "agent-driven development. Overall, this study contributes to "
          "improving the reliability of AI-generated software and provides "
          "a useful foundation for future research and development.")

section_head(doc, "5.3 Contributions to Knowledge")
body(doc, "This study makes the following contributions:")
for c in [
    "A formalisation of eleven failure dimensions as testable engineering "
    "invariants with deterministic rules, calibrated confidence, and "
    "mandatory line-level evidence.",
    "A working guardrail server exposing the framework as thirteen typed "
    "Model Context Protocol tools at zero model-token cost.",
    "A reproducible evaluation method: frozen prompts, hashed manifests, "
    "ten scored criteria, and tables that regenerate from artifacts.",
    "Empirical evidence from seventeen matched agent pairs that guardrailed "
    "generation is measurably more resilient, including a documented "
    "adversarial boundary where heuristics stop.",
    "A practical benefit to developers and small teams: prevention of the "
    "duplicate-charge, lost-update, and partial-state incidents that "
    "otherwise arrive as support tickets."]:
    para_text = doc.add_paragraph(style="List Number")
    para_text.paragraph_format.space_after = __import__(
        "docx.shared", fromlist=["Pt"]).Pt(4)
    run = para_text.add_run(c)
    run.font.name = "Times New Roman"
    run.font.size = __import__("docx.shared", fromlist=["Pt"]).Pt(12)
body(doc, "Where automation of existing evaluation frameworks was the goal "
          "elsewhere (Jahic et al., 2024), this study checks generated code "
          "directly; where studies of architectural decisions in AI systems "
          "observed practice (Zhang et al., 2023), this study intervenes in "
          "it.")
cite(doc, "jahic2024", "zhang2023")

section_head(doc, "5.4 Recommendations")
body(doc, "Based on the findings of this study, the following "
          "recommendations are made:")
for who, what, why in [
    ("Teams using coding agents",
     "route every generated change through plan review before implementation "
     "and code review after, since the largest gains appear before code exists.",
     "plan-level findings reshaped designs while code-level findings only patched them."),
    ("Tool builders",
     "expose checks as typed, deterministic tools with evidence rather than "
     "as model-judged scores.",
     "deterministic output is reproducible, auditable, and free, while judged "
     "scores inherit model unreliability."),
    ("Software engineering educators",
     "teach failure modes as named, checkable properties using the eleven "
     "dimensions and the adversarial set.",
     "named properties convert tacit incident knowledge into testable curriculum."),
    ("Future researchers",
     "replace the two acknowledged heuristic gaps with AST-level analysis "
     "and enforce tool use at the protocol level.",
     "the adversarial results locate exactly where pattern matching stops.")]:
    body(doc, f"{who} should {what} This is necessary because {why}")
body(doc, "These recommendations align with architecture practice, which "
          "holds that decisions should be explicit, reviewable, and tied to "
          "their rationale (Bass, Clements, & Kazman, 2022).")
cite(doc, "bass2022")

section_head(doc, "5.5 Future Work")
body(doc, "No study is completely exhaustive. Future research may consider:")
for f in [
    "AST-level rule analysis to close the lock-scope and acknowledgement-ordering gaps.",
    "Protocol-level enforcement so tool use is not an instruction the agent may ignore.",
    "Dynamic execution of generated systems against failing providers.",
    "Wider scenario coverage across languages beyond Python."]:
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = __import__(
        "docx.shared", fromlist=["Pt"]).Pt(4)
    run = p.add_run(f)
    run.font.name = "Times New Roman"
    run.font.size = __import__("docx.shared", fromlist=["Pt"]).Pt(12)
body(doc, "These enhancements have the potential to improve the "
          "functionality, generality, and real-world validity of the "
          "proposed system.")

doc.save(str(STAGE5))
print(f"Saved {STAGE5}")
(STAGE5.parent / "stage_ch5.cited.json").write_text(
    __import__("json").dumps(CITED), encoding="utf-8")
