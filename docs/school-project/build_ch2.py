"""Chapter 2 of the Failures final-year project report. Appends to the .docx."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from common import (CITED, OUT, STAGE_DIR, body, chapter_head, cite, new_document,
                    page_break, section_head)

STAGE2 = STAGE_DIR / "stage_ch2.docx"
doc = new_document()
chapter_head(doc, "CHAPTER TWO: LITERATURE REVIEW")

section_head(doc, "2.0 Introduction to Chapter Two")
body(doc, "This chapter reviews existing knowledge relevant to deterministic "
          "failure-mode guardrails for AI-generated software. It defines the "
          "concepts in the project title, sets out the theoretical position "
          "of the study, critically reviews related empirical studies, "
          "compares them in a single table, and states the research gap the "
          "present study fills.")
cite(doc)

section_head(doc, "2.1 Introduction")
body(doc, "The purpose of this literature review is not to copy previous "
          "studies but to critically evaluate existing knowledge, identify "
          "research gaps, and justify the need for the present study. It "
          "answers what concepts underpin the study, what previous "
          "researchers achieved with which technologies, what limitations "
          "their work carries, what gap remains, and how this study addresses "
          "that gap. The chapter is organised into a conceptual review of "
          "every major concept in the project title, a theoretical review, "
          "an empirical review of nineteen studies, a comparative analysis, "
          "and the research gap.")

section_head(doc, "2.2 Conceptual Review")
body(doc, "Each concept below follows the same structure: definition with at "
          "least two scholarly sources, explanation, advantages, limitations, "
          "applications, and relationship to the current study.")

# ------------------------------------------------------------- Concept 1
section_head(doc, "2.2.1 Failure and Failure Modes")
body(doc, "Failure refers to any deviation in which a system cannot guarantee "
          "that an operation\u2019s intended effect occurred exactly once and "
          "the system remains in a valid state. According to Kleppmann "
          "(2017), the defining difficulty of distributed systems is that "
          "the network makes failure detection impossible: unbounded delay "
          "means a timeout reveals nothing about whether a remote effect "
          "occurred. According to Nygard (2018), failures in production "
          "systems arrive as stability threats \u2014 cascading overload, "
          "slow responses poisoning fast ones, and unbalanced capacity "
          "\u2014 each demanding an explicit structural response. A failure "
          "mode is a distinct way such a deviation manifests. This study "
          "distinguishes four: hard failure, in which the operation reports "
          "failure; ambiguous outcome, in which the caller cannot tell "
          "whether a side effect happened; partial success, in which some "
          "steps of a compound operation complete and others do not; and "
          "duplicate execution, in which one logical operation runs more "
          "than once (Kalejaiye, 2026).")
cite(doc, "kleppmann2017", "nygard2018", "kalejaiye2026")
body(doc, "The concept is widely applied in distributed systems design, "
          "payment processing, message queues, and site reliability practice "
          "because naming failure modes is the precondition for handling "
          "them: a system cannot be designed against a failure it has not "
          "named (Kleppmann, 2017; Beyer, Jones, Petoff, & Murphy, 2016). "
          "Its strength is precision; its limitation is that taxonomies "
          "describe rather than prevent, and a taxonomy alone changes no "
          "code. In the context of this study, failure modes are the unit "
          "of analysis: every guardrail rule exists to close exactly one of "
          "them, and the ambiguous outcome is treated as the first-class "
          "object because it generates double charges and lost work.")
cite(doc, "beyer2016")

# ------------------------------------------------------------- Concept 2
section_head(doc, "2.2.2 Determinism in Computing")
body(doc, "A deterministic system is one in which identical inputs always "
          "produce identical outputs. According to Kleppmann (2017), "
          "determinism is the property that makes systems testable and "
          "replayable: deterministic simulation testing derives its power "
          "from the guarantee that a recorded execution can be reproduced "
          "exactly. According to Kalejaiye (2026), a deterministic reasoning "
          "engine is one in which the same code always yields the same "
          "findings, so that a finding which disappears between runs is a "
          "real change in the code rather than stochastic variation.")
cite(doc, "kleppmann2017", "kalejaiye2026")
body(doc, "Determinism is applied in testing, simulation, consensus "
          "protocols, and reproducible builds because it converts "
          "observation into evidence: what happened once will happen again "
          "under the same conditions. Its advantage is auditability; its "
          "limitation is expressiveness, since genuinely uncertain "
          "environments cannot be made deterministic, only bounded. In the "
          "context of this study, determinism is the property that separates "
          "the guardrail engine from the language model it supervises: the "
          "model may vary, but the check must not.")

# ------------------------------------------------------------- Concept 3
section_head(doc, "2.2.3 Software Guardrails")
body(doc, "A software guardrail is a preventive control that constrains a "
          "system to its intended behaviour before harm occurs, rather than "
          "detecting harm afterwards. According to Nygard (2018), stability "
          "patterns such as bulkheads, circuit breakers, and timeouts "
          "function as guardrails: they do not fix failures but bound their "
          "blast radius by construction. According to Kalejaiye (2026), a "
          "failure-mode guardrail is a checkable engineering invariant "
          "paired with a rule, line-level evidence, and a required control, "
          "evaluated before code ships.")
cite(doc, "nygard2018", "kalejaiye2026")
body(doc, "Guardrails are applied in deployment pipelines, API gateways, "
          "infrastructure policy, and increasingly in AI systems, because "
          "prevention is cheaper than incident response and because "
          "constraints that are checked cannot be forgotten the way "
          "conventions can. Their advantage is that they make the right "
          "behaviour the easy behaviour; their limitation is coverage, since "
          "a guardrail only guards what its author anticipated. In the "
          "context of this study, guardrails are the deliverable: eleven "
          "failure dimensions operationalised as rules an agent must satisfy.")

# ------------------------------------------------------------- Concept 4
section_head(doc, "2.2.4 AI-Generated Software and Coding Agents")
body(doc, "AI-generated software is source code produced substantially by "
          "language models rather than written directly by programmers. "
          "According to Chen et al. (2021), large language models trained on "
          "code solve a substantial share of self-contained programming "
          "problems, establishing functional correctness as the measurable "
          "output of generation. According to Peng, Kalliamvakou, Cihon, and "
          "Demirer (2023), professional developers using code assistants "
          "complete tasks measurably faster, confirming that generated code "
          "has entered production workflows rather than remaining a research "
          "demonstration. A coding agent extends generation with tool use: "
          "it writes, executes, and revises code through external tools, and "
          "the Model Context Protocol standardises how such tools are "
          "discovered and invoked (Anthropic, 2024).")
cite(doc, "chen2021", "peng2023", "anthropic2024")
body(doc, "AI-generated software is applied across web backends, data "
          "pipelines, test suites, and prototypes because it compresses the "
          "time from intent to running code. Its advantage is speed; its "
          "limitations are well documented: generated code inherits the "
          "happy-path bias of its training data, benchmarks score "
          "correctness rather than resilience (Jimenez et al., 2024), and "
          "security audits find a substantial share of suggestions "
          "vulnerable (Pearce, Ahmad, Tan, Dolan-Gavitt, & Karri, 2022). In "
          "the context of this study, agent output is both the problem and "
          "the experimental material: the same prompts issued with and "
          "without guardrails produce the compared systems.")
cite(doc, "jimenez2024", "pearce2022")

# ------------------------------------------------------------- Concept 5
section_head(doc, "2.2.5 Model Context Protocol")
body(doc, "The Model Context Protocol is an open protocol that standardises "
          "how a language model discovers and invokes external tools "
          "(Anthropic, 2024). A server exposes typed tools over a uniform "
          "interface; any compliant agent can list them, call them, and "
          "receive structured results. According to Kalejaiye (2026), the "
          "protocol is used in this study as the delivery mechanism for "
          "guardrail checks: thirteen deterministic tools exposed through "
          "one server, callable by any compliant agent, returning findings "
          "with severity, confidence, evidence, and required controls.")
cite(doc, "anthropic2024", "kalejaiye2026")
body(doc, "The protocol is applied wherever models need reliable access to "
          "file systems, databases, and domain tools, because a standard "
          "interface removes per-agent integration work. Its advantage is "
          "portability: one server serves every compliant agent, so an "
          "evaluation across three agents tests one intervention rather than "
          "three integrations. Its limitation is that the protocol carries "
          "calls, not obligations: nothing in it compels an agent to invoke "
          "a tool, which is why this study instructs tool use explicitly and "
          "records it as a protocol limitation. In the context of this study, "
          "the protocol is what makes the comparison fair: the only "
          "difference between study arms is whether the server is connected.")

# ------------------------------------------------------------- Concept 6
section_head(doc, "2.2.6 Software Resilience")
body(doc, "Resilience is the ability of a system to preserve its invariants "
          "under failures. According to Nygard (2018), resilient systems are "
          "designed around the expectation of failure, with explicit controls "
          "for each anticipated mode rather than optimistic assumptions "
          "about the environment. According to Beyer et al. (2016), "
          "resilience is produced organisationally as well as technically, "
          "through postmortems that convert incidents into design "
          "constraints.")
cite(doc, "nygard2018", "beyer2016")
body(doc, "Resilience is pursued in payment systems, messaging "
          "infrastructure, and safety-critical software because the cost of "
          "failure there is measured in money and safety rather than "
          "inconvenience. Its advantage as a goal is that it is testable: an "
          "invariant either holds under a failure or it does not. Its "
          "limitation is that it is unbounded in principle, since no finite "
          "control set covers every failure; the honest response is to name "
          "the covered set explicitly. In the context of this study, "
          "resilience is the dependent variable: ten criteria score it, and "
          "the study succeeds only if the guardrailed systems score higher.")

section_head(doc, "2.3 Theoretical Review")
body(doc, "This study is implementation-oriented and therefore does not rely "
          "on a formal behavioural or theoretical framework. Instead, it is "
          "guided by established computing principles and system development "
          "methodologies: the distributed-systems account of failure and "
          "idempotence (Kleppmann, 2017), the stability-patterns canon "
          "(Nygard, 2018), and Design Science Research as the research "
          "design, which develops and evaluates an innovative computing "
          "artefact rather than testing behavioural hypotheses (Hevner, "
          "March, Park, & Ram, 2004; Peffers, Tuunanen, Rothenberger, & "
          "Chatterjee, 2007). The detailed justification appears in Chapter "
          "Three.")
cite(doc, "kleppmann2017", "nygard2018", "hevner2004", "peffers2007")

# ============================================================ 2.4 empirical
section_head(doc, "2.4 Empirical Review (Review of Related Studies)")

REVIEWS = [
("Chen et al. (2021)",
 "conducted the study \u201cEvaluating large language models trained on code\u201d "
 "with the aim of measuring functional correctness of code-trained models. The "
 "researchers adopted benchmark evaluation on held-out programming problems and "
 "implemented the HumanEval set using pass-at-k scoring. The study found that "
 "large models solve a substantial share of self-contained problems. However, "
 "the research was limited to functional correctness on exercised paths, with no "
 "measurement of failure handling. Unlike the present study, which scores "
 "resilience under failures, their work established the correctness baseline "
 "this study departs from."),
("Pearce et al. (2022)",
 "conducted the study \u201cAsleep at the keyboard? Assessing the security of "
 "GitHub Copilot\u2019s code contributions\u201d with the aim of auditing the "
 "security of generated code. The researchers adopted systematic security "
 "review of Copilot suggestions across vulnerability classes. The study found "
 "that a substantial share of suggestions was vulnerable. However, the research "
 "was limited to security defects in snippets rather than failure handling in "
 "systems. Unlike the present study, which checks resilience properties of "
 "complete agent outputs, their work audited fragments for known weaknesses."),
("Peng et al. (2023)",
 "conducted the study \u201cThe impact of AI on developer productivity: "
 "Evidence from GitHub Copilot\u201d with the aim of measuring productivity "
 "effects of code assistants. The researchers adopted telemetry analysis of "
 "professional developers with and without assistance. The study found "
 "measurable task-completion gains. However, the research was limited to speed "
 "and acceptance metrics, with no measurement of the quality or resilience of "
 "what was produced faster. Unlike the present study, which asks whether "
 "faster output is also safer output, their work measured velocity alone."),
("Jimenez et al. (2024)",
 "conducted the study \u201cSWE-bench: Can language models resolve real-world "
 "GitHub issues?\u201d with the aim of benchmarking models on genuine "
 "repository problems. The researchers adopted issue-resolution scoring on "
 "real pull requests with hidden tests. The study found that models resolve a "
 "growing share of real issues. However, the research was limited to whether "
 "issues resolve, not whether resolutions survive failures. Unlike the present "
 "study, which scores the resilience of finished systems, their work moved "
 "evaluation toward realism without changing its axis."),
("Schmid et al. (2025)",
 "conducted the study \u201cSoftware Architecture Meets LLMs: A Systematic "
 "Literature Review\u201d with the aim of mapping language-model applications "
 "in software architecture. The researchers adopted systematic literature "
 "review. The study found that models translate requirements into diagrams "
 "effectively but hallucinate as a central limitation. However, the research "
 "was limited to surveying rather than building. Unlike the present study, "
 "which replaces the hallucinating judge with deterministic checks, their work "
 "documented the problem this study answers."),
("Konersmann et al. (2022)",
 "conducted the study of evaluation methods and replicability of software "
 "architecture research objects with the aim of mapping how the field "
 "evaluates. The researchers adopted systematic review of ICSA and ECSA "
 "papers. The study found that experiments and case studies dominate while "
 "only a small minority of papers ship replication packages. However, the "
 "research was limited to two conference venues. Unlike the present study, "
 "which ships frozen prompts, manifests, and regenerable tables, their work "
 "described the reproducibility deficit this study is designed against."),
("Farshidi and Jansen (2020)",
 "conducted the study \u201cA decision support system for pattern-driven "
 "software architecture\u201d with the aim of automating pattern selection. "
 "The researchers adopted multi-criteria decision making over a knowledge "
 "base. The study found that requirements match to patterns adequately. "
 "However, the research was limited to strict technical quality requirements "
 "without capability reasoning. Unlike the present study, which checks failure "
 "properties of generated code, their work selected patterns for stated "
 "requirements."),
("Öqvist et al. (2024)",
 "conducted the study \u201cSupporting early architectural decision-making "
 "through trade-off analysis\u201d with the aim of making decisions explicit. "
 "The researchers adopted experimental implementation at an automotive firm. "
 "The study found that explicit trade-off visualisation reduced rework. "
 "However, the research was limited to one industry context. Unlike the "
 "present study, which evaluates guardrailed agent output across scenarios, "
 "their work improved human decisions rather than checking machine output."),
("Ajoudanian and Abadeh (2024)",
 "conducted the study \u201cCapability-driven framework to automate discovery "
 "of bounded contexts\u201d with the aim of structuring requirements through "
 "capabilities. The researchers adopted domain-driven design. The study found "
 "that capability-driven structuring aligns business and software. However, "
 "the research was limited to the requirements phase without downstream "
 "checking. Unlike the present study, which verifies properties of finished "
 "code, their work stopped at structuring intent."),
("Bucaioni et al. (2025)",
 "conducted the study \u201cArtificial Intelligence for Software Architecture: "
 "Literature Review and the Road Ahead\u201d with the aim of mapping AI "
 "applications in architecture. The researchers adopted literature review. The "
 "study found adoption to be at an early stage. However, the research did not "
 "assess practical application or build anything. Unlike the present study, "
 "which implements and evaluates a working guardrail server, their work "
 "surveyed the territory."),
("Esposito et al. (2025)",
 "conducted the study \u201cGenerative AI for Software Architecture\u201d "
 "with the aim of mapping generative applications, trends, and challenges. "
 "The researchers adopted analytical survey. The study found that models "
 "generate plausible draft architectures. However, the research assessed only "
 "theoretical possibility while practical tools remain non-deterministic. "
 "Unlike the present study, which enforces determinism in the checking layer, "
 "their work explored what generative models might do."),
("Eisenreich et al. (2024)",
 "conducted the study \u201cFrom Requirements to Architecture\u201d with the "
 "aim of semi-automating architecture generation. The researchers adopted "
 "AI-based tool implementation. The study found reduced design effort. "
 "However, the research required well-structured inputs. Unlike the present "
 "study, which checks arbitrary agent output for missing properties, their "
 "work generated architectures from clean requirements."),
]
for head, text in REVIEWS:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(head + " ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r2 = p.add_run(text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
cite(doc, "chen2021", "pearce2022", "peng2023", "jimenez2024", "schmid2025",
     "konersmann2022", "farshidi2020", "oqvist2024", "ajoudanian2024",
     "bucaioni2025", "esposito2025", "eisenreich2024")

REVIEWS2 = [
("Dake et al. (2021)",
 "conducted the study \u201cTraffic Engineering in Software-defined Networks "
 "using Reinforcement Learning: A Review\u201d with the aim of structuring "
 "knowledge on intelligent traffic control. The researchers adopted literature "
 "review. The study found that intelligent agents optimise congestion. "
 "However, the research was confined to network traffic. Unlike the present "
 "study, which addresses software failure resilience generally, their work "
 "stayed within one networked domain. Studied in Ghana, it shows the "
 "continent\u2019s active presence in applied systems research."),
("Ndifor et al. (2021)",
 "conducted the research \u201cUsing Experiential Learning to Improve Student "
 "Attitude and Learning Quality in Software Engineering Education\u201d with "
 "the aim of testing active learning quantitatively. The researchers adopted "
 "PLS-SEM analysis of student cohorts. The study found that practical "
 "involvement improves architecture learning. However, the research was "
 "confined to educational contexts. Unlike the present study, which evaluates "
 "production-style systems, their work measured classroom outcomes."),
("Bernard et al. (2020)",
 "conducted the study on architectural design requirement specifications for "
 "an intelligent tutor system with the aim of assessing what documentation "
 "aids construction. The researchers adopted quantitative survey of lecturers "
 "and developers in Nigerian universities. The study found that "
 "well-documented requirements facilitate building. However, the research was "
 "limited to a small local sample. Unlike the present study, which evaluates "
 "at enterprise-relevant scope, their work demonstrates the Nigerian "
 "relevance of documentation discipline."),
("Oliha (2022)",
 "conducted the study \u201cGuaranteeing Performance in a Fault Tolerant "
 "Architecture Solution using Software Agent\u2019s Coordination\u201d with "
 "the aim of designing a fault-tolerant architecture. The author adopted "
 "simulation. The study found that replication and diversity improve "
 "performance. However, the research was validated only on synthetic "
 "requests. Unlike the present study, which evaluates a working guardrail "
 "system on concrete scenarios, this work analysed fault tolerance "
 "conceptually."),
("Oliha (2022)",
 "also assessed the performability of fault-tolerant web-service "
 "architectures through compile-time software fault injection, finding that "
 "agent-based coordination improves response characteristics. The limitation "
 "remained the restriction to web services. Unlike the present study, whose "
 "findings apply across backend system types, this work stayed within one "
 "architectural style."),
("Matthew et al. (2024)",
 "conducted the research \u201cGreen Software Engineering Development "
 "Paradigm\u201d with the aim of mapping sustainability principles into "
 "decision structures. The authors adopted conceptual review. The study found "
 "that green principles belong inside organisational decision-making, but "
 "proposed no quantitative model for trade-off analysis. Unlike the present "
 "study, which quantifies its criteria and scores them, their work stayed at "
 "the paradigm level."),
("Onoja et al. (2024)",
 "conducted the research on hDevOps and sustainable software engineering with "
 "the aim of balancing delivery speed with reliability and environmental "
 "responsibility. The authors adopted literature review with case analysis. "
 "The study found energy-conscious pipelines viable. However, the research "
 "was limited to CI/CD operations. Unlike the present study, which checks "
 "failure properties of delivered systems, their work optimised the delivery "
 "machinery itself."),
]
for head, text in REVIEWS2:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(head + " ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r2 = p.add_run(text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
cite(doc, "dake2021", "ndifor2021", "bernard2020", "oliha2022a",
     "oliha2022b", "matthew2024", "onoja2024")

# ------------------------------------------------- 2.5 comparative table
section_head(doc, "2.5 Comparative Analysis of Reviewed Studies")
body(doc, "The reviewed literature demonstrates that several studies have "
          "investigated failure handling, code generation, and architecture "
          "decision support using various methodologies. Although these "
          "studies have made significant contributions, limitations such as "
          "correctness-only evaluation, non-deterministic judges, and "
          "missing failure-property checking remain. A summary of the "
          "reviewed literature is presented in Table 2.1.")

TABLE_ROWS = [
 ("Chen et al.", "2021", "Measure code-model correctness", "Benchmark",
  "Models solve many problems", "Correctness only", "No resilience scoring"),
 ("Pearce et al.", "2022", "Audit Copilot security", "Security review",
  "Many suggestions vulnerable", "Snippets, not systems", "No failure checks"),
 ("Peng et al.", "2023", "Measure Copilot productivity", "Telemetry",
  "Faster completion", "Speed only", "Quality unmeasured"),
 ("Jimenez et al.", "2024", "Benchmark real-issue repair", "Issue tests",
  "Growing resolution rates", "Resolution, not resilience", "No failure axis"),
 ("Schmid et al.", "2025", "Map LLMs in architecture", "Review",
  "Translation works; hallucination central", "Survey only", "No checking layer"),
 ("Konersmann et al.", "2022", "Map evaluation practice", "Review",
  "Experiments dominate; few replications", "Two venues", "Reproducibility gap"),
 ("Farshidi & Jansen", "2020", "Automate pattern selection", "MCDM + KB",
  "Matched requirements to patterns", "Rigid criteria", "No failure properties"),
 ("Öqvist et al.", "2024", "Explicit trade-off analysis", "Experiment",
  "Rework reduced", "One industry", "Human decisions, not machine output"),
 ("Ajoudanian & Abadeh", "2024", "Capability-driven structuring", "DDD",
  "Aligned business and software", "Requirements only", "No downstream checks"),
 ("Bucaioni et al.", "2025", "Survey AI in architecture", "Review",
  "Adoption early-stage", "No building", "No evaluated artefact"),
 ("Esposito et al.", "2025", "Map generative applications", "Survey",
  "Plausible drafts", "Non-deterministic", "No determinism enforced"),
 ("Eisenreich et al.", "2024", "Generate architecture from requirements",
  "Tool build", "Less design effort", "Needs clean inputs", "No output checking"),
 ("Dake et al.", "2021", "Review RL traffic engineering", "Review",
  "Agents optimise congestion", "Networks only", "Single domain"),
 ("Ndifor et al.", "2021", "Test active learning", "PLS-SEM",
  "Practice improves learning", "Classroom only", "Not production systems"),
 ("Bernard et al.", "2020", "Assess tutor-system specs", "Survey",
  "Documentation aids building", "Small local sample", "Local scope only"),
 ("Oliha", "2022", "Fault-tolerant architecture", "Simulation",
  "Replication helps", "Synthetic only", "Conceptual, no guardrails"),
 ("Oliha", "2022", "Web-service performability", "Fault injection",
  "Better response", "Web services only", "One style only"),
 ("Matthew et al.", "2024", "Green SE paradigm", "Conceptual",
  "Principles mapped", "No quantification", "No scored criteria"),
 ("Onoja et al.", "2024", "Sustainable hDevOps", "Review + cases",
  "Viable pipelines", "CI/CD only", "Delivery, not delivered systems"),
]
table = doc.add_table(rows=1 + len(TABLE_ROWS), cols=7)
table.style = "Table Grid"
hdr = ["Author(s)", "Year", "Aim", "Methodology", "Findings", "Limitations",
       "Research Gap"]
widths = [1.0, 0.5, 1.0, 0.9, 1.0, 0.9, 1.0]
for j, h in enumerate(hdr):
    cell = table.cell(0, j)
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(h)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(9)
for i, row in enumerate(TABLE_ROWS, start=1):
    for j, val in enumerate(row):
        cell = table.cell(i, j)
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(val)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        cell.width = int(widths[j] * 914400)
para_text = doc.add_paragraph()
para_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = para_text.add_run("Table 2.1: Comparative Analysis of Reviewed Studies")
run.bold = True
run.font.name = "Times New Roman"
run.font.size = Pt(12)

section_head(doc, "2.6 Research Gap")
body(doc, "The reviewed literature indicates that significant progress has "
          "been made in code generation, architecture decision support, and "
          "failure analysis. Previous studies have successfully addressed "
          "functional evaluation, pattern selection, and resilience "
          "cataloguing. However, limitations such as correctness-only "
          "metrics, non-deterministic judges, and missing failure-property "
          "checking remain unresolved. No study has yet "
          "connected deterministic failure-mode guardrails to the coding "
          "agents that produce the systems. Therefore, this study seeks to "
          "address these limitations by designing, implementing, and "
          "evaluating a guardrail system that checks named failure modes "
          "with evidence before agent-generated code ships.")

doc.save(str(STAGE2))
print(f"Saved {STAGE2} — ch2 staged")

(STAGE_DIR / "stage_ch2.cited.json").write_text(__import__("json").dumps(CITED), encoding="utf-8")
