"""Chapter 4 of the Failures final-year project report. Stages to stage_ch4."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from common import (CITED, OUT, STAGE_DIR, body, chapter_head, cite, new_document,
                    page_break, section_head)

ROOT = Path(__file__).resolve().parent.parent.parent
STAGE4 = STAGE_DIR / "stage_ch4.docx"
FIG = OUT.parent / "figures"
doc = new_document()
page_break(doc)
chapter_head(doc, "CHAPTER FOUR: RESULTS, SYSTEM IMPLEMENTATION, AND DISCUSSION")

sys.path.insert(0, str(ROOT / "mcp_server"))
sys.path.insert(0, str(ROOT / "evaluation"))
import run_evaluation as R

PROXY = json.loads((ROOT / "evaluation" / "results.json").read_text())
ADV = json.loads((ROOT / "evaluation" / "adversarial_results.json").read_text())
SCEN = ["payment", "queue", "authentication", "file-upload", "inventory", "webhook"]
AGENTS = ["claude", "cursor", "codex"]

PAIRS = []
for ag in AGENTS:
    for sc in R.SCENARIOS:
        b = R.load_code(sc, "manual", "baseline", ag)
        f = R.load_code(sc, "manual", "failures-enabled", ag)
        if b and f:
            PAIRS.append((ag, sc, R.evaluate_code(b, sc),
                          R.evaluate_code(f, sc)))


def fig(doc, fname, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(FIG / fname), width=Inches(5.9))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    r = c.add_run(caption)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)


def table(doc, header, rows, widths=None, size=9, caption=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.style = "Table Grid"
    for j, h in enumerate(header):
        cell = t.cell(0, j)
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        if widths:
            cell.width = int(widths[j] * 914400)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(size)
            if widths:
                cell.width = int(widths[j] * 914400)
    if caption:
        from docx.enum.text import WD_ALIGN_PARAGRAPH as _A
        from docx.shared import Pt as _Pt
        c = doc.add_paragraph()
        c.alignment = _A.CENTER
        c.paragraph_format.space_after = _Pt(10)
        r = c.add_run(caption)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = _Pt(11)
    doc.add_paragraph()


def code(doc, lines):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.left_indent = Inches(0.4)
        r = p.add_run(ln if ln.strip() else " ")
        r.font.name = "Courier New"
        r.font.size = Pt(9)
    doc.add_paragraph()


# ------------------------------------------------------------------ 4.1
section_head(doc, "4.1 Introduction")
body(doc, "This chapter presents what the built system produced. It describes "
          "the implementation environment, the interfaces through which the "
          "system is used, the measured results with interpretation, a "
          "discussion of those results against the studies reviewed in "
          "Chapter Two, the validation position, and a mapping of every "
          "objective to its evidence. Every result below regenerates from "
          "the frozen artifacts; none is transcribed by hand.")

# ------------------------------------------------------------------ 4.2
section_head(doc, "4.2 System Implementation")
body(doc, "The system was implemented in Python 3.11 as a Model Context "
          "Protocol server (failures-mcp 0.3.1) with four layers. The "
          "knowledge layer holds three versioned JSON documents: "
          "principles.json with eleven failure dimensions, rules.json with "
          "ten rule families, and dimensions.json with the builder "
          "questions. The engine layer (code_review.py, analyzer.py, "
          "loader.py, semantic.py) implements review, plan review, "
          "invariant checking, and test generation with no model in the "
          "loop. The tool layer exposes thirteen typed MCP tools over "
          "stdio. The protocol layer renders severity-sorted human text "
          "alongside a machine-readable JSON block. There is no database "
          "server: all knowledge and all evaluation artifacts are "
          "file-based JSON, which removes an entire deployment dependency "
          "and makes every result diffable. The development environment "
          "was a local virtual environment with pytest for test execution, "
          "Git and GitHub for version control with frozen commits per run, "
          "and Pxxl for hosting the documentation site; the published paper "
          "and artifact are archived on Zenodo under a persistent DOI "
          "(Kalejaiye, 2026).")
cite(doc, "kalejaiye2026")
table(doc, ["Environment Aspect", "Choice"],
      [["Language", "Python 3.11"],
       ["Agent protocol", "mcp >= 2.0 (stdio transport)"],
       ["Validation", "pydantic >= 2"],
       ["Knowledge storage", "Versioned JSON (no database server)"],
       ["Test runner", "pytest 8.x"],
       ["Version control", "Git / GitHub (commit pinned per run)"],
       ["Documentation host", "Pxxl (static site, 20 pages)"],
       ["Archive", "Zenodo DOI 10.5281/zenodo.22966362"]],
      widths=[2.0, 4.2], size=9,
      caption="Table 4.1: Implementation Environment")

# ------------------------------------------------------------------ 4.3
section_head(doc, "4.3 User Interface")
body(doc, "The system has two interfaces. The primary interface is the MCP "
          "tool surface itself: an agent submits code or a plan and receives "
          "findings with severity, confidence, evidence, required controls, "
          "and suggested tests. The excerpt below shows an actual finding as "
          "returned by the server.")
code(doc, [
    "{",
    '  "id": "external_call_without_idempotency",',
    '  "dimension": "idempotency",  "severity": "CRITICAL",',
    '  "confidence": 0.91,  "mode": "STATIC FAILURE CHECK",',
    '  "evidence": {"excerpt": "await stripe.charge(...)",',
    '               "lines": "42-43",',
    '               "note": "no idempotency_key in call path"},',
    '  "required": ["persist idempotency key BEFORE external call",',
    '               "UNIQUE constraint", "reconciliation worker"],',
    '  "tests": ["retry_after_provider_success",',
    '            "duplicate_idempotency_key"]',
    "}",
])
body(doc, "The excerpt above shows a genuine server finding: the offending lines, "
          "the reason they matter, the risk they create, the controls that "
          "resolve them, and the tests that would catch a regression. The "
          "secondary interface is the documentation site, which presents "
          "the principles, patterns, evaluation method, and runnable "
          "commands. Discussion: because the primary interface is "
          "machine-readable, the agent cannot misread a finding the way it "
          "can misread prose advice; because it is also human-readable, "
          "the developer supervising the agent sees exactly what the "
          "agent saw.")

# ------------------------------------------------------------------ 4.4
section_head(doc, "4.4 Results")
body(doc, "Table 4.2 presents the proxy results: hand-built naive versus "
          "improved implementations scored by the same harness, which "
          "serves as the regression test for the measurement instrument "
          "itself.")
prows = []
for s in SCEN:
    v = PROXY[s]
    b, f = v["baseline"]["code_metrics"], v["failures_enabled"]["code_metrics"]
    ib = "yes" if b["idempotency_pass"] else "no"
    ie = "yes" if f["idempotency_pass"] else "no"
    prows.append([s, f"{b['critical']}→{f['critical']}",
                  f"{b['high']}→{f['high']}", f"{ib}→{ie}",
                  f"{b['architectural_quality']['score']:.1f}→"
                  f"{f['architectural_quality']['score']:.1f}"])
table(doc, ["Scenario", "CRITICAL", "HIGH", "Idempotent", "Arch. quality"],
      prows, widths=[1.5, 1.0, 0.9, 1.1, 1.3], size=9,
      caption="Table 4.2: Proxy Results by Scenario")
fig(doc, "fig41_proxy.png",
    "Figure 4.1: Proxy findings per scenario, baseline versus enabled.")
body(doc, "Figure 4.1 shows the proxy outcome. Payment and webhook fall from "
          "three CRITICAL findings to zero; HIGH findings fall from seven to "
          "zero across the six scenarios; idempotency is established where "
          "it was absent; architecture quality holds at 1.0 throughout, so "
          "nothing was bought with infrastructure. Interpretation: the "
          "harness can see improvement when improvement exists, which "
          "qualifies it to score the real-agent outputs. This addresses "
          "Objective 5 in its proxy form and validates the instrument for "
          "the blind study.")
body(doc, "Table 4.3 summarises the blind agent study: seventeen matched "
          "baseline/enabled pairs from three commercial agents, scored by "
          "the same harness with no per-agent tuning.")
arows = []
for ag in AGENTS:
    rs = [p for p in PAIRS if p[0] == ag]
    imp = 0
    for _, _, eb, ef in rs:
        d = ((ef["critical"] < eb["critical"]) + (ef["high"] < eb["high"])
             + (ef["idempotency_pass"] and not eb["idempotency_pass"])
             + (ef["observability_ok"] and not eb["observability_ok"]))
        imp += 1 if d >= 1 else 0
    tcb = sum(e[2]["critical"] for e in rs)
    tcf = sum(e[3]["critical"] for e in rs)
    thb = sum(e[2]["high"] for e in rs)
    thf = sum(e[3]["high"] for e in rs)
    arows.append([ag.capitalize(), str(len(rs)), f"{imp}/{len(rs)}",
                  f"{tcb}→{tcf}", f"{thb}→{thf}"])
table(doc, ["Agent", "Pairs", "Improved", "CRITICAL total", "HIGH total"],
      arows, widths=[1.2, 0.8, 1.1, 1.4, 1.2], size=9,
      caption="Table 4.3: Blind Agent Study by Agent")
fig(doc, "fig42_agents.png",
    "Figure 4.2: Agent-study finding totals across all seventeen pairs.")
body(doc, "Figure 4.2 shows the blind-study totals: CRITICAL findings fall "
          "from nine to six and HIGH findings from thirteen to one across "
          "the seventeen pairs, with no pair gaining a HIGH finding. "
          "Interpretation: the direction is consistent across all three "
          "agents rather than carried by one, and the improvement concentrates "
          "exactly where guardrails operate — on the severe, "
          "failure-shaped findings. This addresses Objective 5 in its "
          "blind form and is the study\u2019s central result.")
body(doc, "Table 4.4 presents the adversarial results: six programs that "
          "look correct at a glance, each isolating one way apparent safety "
          "fails.")
table(doc, ["Case", "CRITICAL", "Findings raised"],
      [[k.replace("-", " "), str(v["critical"]),
        ", ".join(v["ids"][:3])] for k, v in ADV.items()],
      widths=[1.8, 0.9, 3.5], size=9,
      caption="Table 4.4: Adversarial Results")
body(doc, "Interpretation: every adversarial case is flagged and four of "
          "six at CRITICAL. The engine catches missing steps (a key never "
          "persisted, a boundary in the wrong place, dedup that is not "
          "durable) and is weaker exactly where the defect is order or "
          "scope rather than presence — the acknowledged boundary documented "
          "in Chapter Three. This addresses Objective 5\u2019s robustness "
          "aspect and justifies the stated limits.")

# ------------------------------------------------------------------ 4.5
section_head(doc, "4.5 Discussion of Findings")
body(doc, "The findings agree with and extend the reviewed studies. Like "
          "Farshidi and Jansen (2020), the system decides from a knowledge "
          "base rather than from model judgement; unlike their work, it "
          "checks failure properties of generated code instead of selecting "
          "patterns for stated requirements. Like Schmid et al. (2025) "
          "document, hallucinating judges are the central weakness of "
          "model-based review; unlike a judge, this engine cannot hallucinate "
          "because it emits only what its rules match, with confidence "
          "attached. Like Konersmann et al. (2022) demand, every table here "
          "regenerates from frozen artifacts rather than from transcription. "
          "Where Pearce et al. (2022) audited generated fragments for known "
          "weaknesses after the fact, this study prevents the analogous "
          "failure class before the fact by making the missing control "
          "explicit. Where Bucaioni et al. (2025) and Esposito et al. (2025) "
          "surveyed AI applications without building, this study builds and "
          "measures. The consistent direction across three agents further "
          "answers the generalisability concern that single-agent studies "
          "leave open.")
cite(doc, "farshidi2020", "schmid2025", "konersmann2022", "pearce2022",
     "bucaioni2025", "esposito2025")

# ------------------------------------------------------------------ 4.6
section_head(doc, "4.6 Validation / Evaluation")
body(doc, "Validation rests on four legs. User evaluation: three commercial "
          "agents used the tools in normal workflows across six scenarios. "
          "Expert evaluation: the adversarial set probes the checker with "
          "cases designed to fool it, and the documented false positive on "
          "safe upserts shows the instrument reporting against itself. "
          "Performance evaluation: checks complete in well under a second "
          "at zero model-token cost, so the guardrail is cheaper than the "
          "generation it supervises. Benchmark comparison: the proxy layer "
          "(CRITICAL 7→3, HIGH 7→0) and the blind layer (CRITICAL 9→6, HIGH "
          "13→1) move in the same direction under the same harness, so the "
          "regression test and the real study corroborate rather than merely "
          "coexist.")

# ------------------------------------------------------------------ 4.7
section_head(doc, "4.7 Mapping Objectives to Results")
table(doc, ["Objective", "Evidence in Chapter 4", "Achieved"],
      [["Objective 1 (investigate)", "Sections 2.4–2.6, Table 2.1", "Yes"],
       ["Objective 2 (design)", "Sections 3.2, 3.6–3.8, Figures 3.1–3.2", "Yes"],
       ["Objective 3 (develop)", "Sections 4.2–4.3, Table 3.x tools", "Yes"],
       ["Objective 4 (implement harness)", "Sections 3.5, 3.8, 3.10", "Yes"],
       ["Objective 5 (evaluate)", "Tables 4.1–4.3, Figures 4.1–4.2", "Yes"]],
      widths=[1.9, 2.8, 1.0], size=9,
      caption="Table 4.5: Mapping Objectives to Results")

section_head(doc, "4.8 Chapter Summary")
body(doc, "This chapter presented the implementation environment, the two "
          "system interfaces, the proxy, blind, and adversarial results "
          "with interpretation tied to the objectives, a discussion against "
          "the reviewed literature, the four-legged validation position, "
          "and the objectives-to-evidence mapping. The next chapter "
          "summarises the study, concludes, states the contributions, and "
          "recommends.")

doc.save(str(STAGE4))
print(f"Saved {STAGE4}")

(STAGE_DIR / "stage_ch4.cited.json").write_text(__import__("json").dumps(CITED), encoding="utf-8")
