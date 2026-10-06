# Likely Defence Questions — Failures Final-Year Project

Model answers below are spoken-length (45–75 seconds each). Every answer
is grounded in the submitted report — nothing here goes beyond what is
already written and evidenced there. If the panel asks anything else,
anchor back to one of these.

## 1. "Why deterministic rules instead of just asking an LLM to review the code?"

Because the judge inherits the disease it is meant to diagnose. An LLM
reviewer is stochastic, costs tokens on every call, and hallucinates
defects — our review cites the Copilot audit and the architecture-LLM
survey on exactly this. A deterministic rule emits only what it matches,
with confidence attached, at zero token cost. And there is a methodological
reason: if a second model call did the work, any improvement could be
explained as extra reasoning effort rather than the intervention. With a
deterministic checker, the only difference between study arms is whether
the server was connected.

## 2. "Your engine is pattern matching. Isn't that too weak for real guarantees?"

Yes — for some guarantees, and the report says so explicitly. The engine
cannot prove lock scope or acknowledgement ordering; the adversarial set
locates that boundary precisely, with two of six cases flagged at HIGH
rather than CRITICAL. But weakness in general is not weakness everywhere:
persisted-before-call, wrapped-in-transaction, and unique-constraint
checks are syntactic questions with syntactic answers, and those cover the
double-charge and lost-update classes that dominate the incidents. The
claim was never soundness — it is calibrated, evidenced checking with
honest confidence labels.

## 3. "Seventeen pairs is a small sample. How do you generalise?"

Cautiously, and the report does. The claim is directional consistency
across three agents, not a population estimate: 16 of 17 improve, HIGH
never rises in any pair, and the direction holds per agent (6/6, 5/5,
5/6). Six scenarios cover distinct failure shapes — payments, queues,
auth, uploads, inventory, webhooks. Generalisation beyond Python web
backends is explicitly listed as future work, not claimed.

## 4. "Only Python? What about other languages?"

Correct, and stated as a scope limit in Section 1.5. The rule engine
matches Python source structure, and the entire evaluation corpus is
Python. The framework — principles, invariants, harness design — is
language-agnostic, and porting rules is listed as future work. Nothing in
the conclusions depends on Python-specific behaviour.

## 5. "Five pairs regressed. Doesn't that undermine the claim?"

No — it sharpens it, and the report discusses all five rather than hiding
them. Two kinds: one is the documented upsert false positive (a safe
`ON CONFLICT` counted as a non-transactional write), which is the
strongest single argument for AST-level rules. The other three are the
tool catching the agent at something real — retry logic added without
idempotency, which the engine then correctly flags as unsafe retry. A
checker that never fires on the intervention arm would be more
suspicious than one that does.

## 6. "Why these three agents? Why not more?"

Three commercial agents from different vendors so the result is not an
artifact of one model's habits. Same six prompts, same harness, no
per-agent tuning. The direction holds for all three, which is the
invariance the study needed. More agents would strengthen it and is
listed as future work — but the per-agent consistency already rules out
the single-model confound.

## 7. "What is actually novel here? Static analysers already exist."

Two things analysers do not do. First, they do not encode engineering
intent: a dataflow analyser finds uninitialised values, not missing
idempotency keys on payment handlers. Our rules encode invariants —
properties that must hold under any failure. Second, analysers are not
delivered to agents as tools at the point of generation. The novelty is
the combination held to an empirical standard: machine-checkable failure
resilience, delivered at generation time, evaluated blind.

## 8. "How is this different from a linter?"

A linter checks style and syntax against generic rules and cries wolf
until engineers ignore it. Three differences: our rules encode domain
intent (invariants, not style); every finding carries line evidence,
severity, confidence, required controls, and tests; and confidence is
calibrated, with `BUG PROVEN` reserved for syntactic proofs. The design
goal was a tool an engineer learns to trust, not one they learn to
dismiss.

## 9. "Your proxy study uses hand-written code. Isn't that circular?"

The proxy is a regression test for the instrument, not evidence about
agents — and the report states this explicitly. Its job is to prove the
harness can see improvement where improvement is known to exist, which
qualifies it to score the blind study. The evidential weight rests
entirely on the seventeen real-agent pairs, which no author wrote.

## 10. "What would you do with six more months?"

Four items, in order, all listed in Section 5.5: AST-level analysis to
close the lock-scope and acknowledgement-ordering gaps the adversarial
set exposed; protocol-level enforcement so tool use is not an
instruction the agent may ignore; dynamic execution of generated systems
against failing providers; wider scenario and language coverage. None
requires changing the model, the knowledge base, or the interface —
only the depth of the checker.

## 11. "Explain ambiguous outcome versus hard failure, with an example."

A hard failure reports itself: a 500, an exception, an explicit
rejection — the caller knows. An ambiguous outcome hides: Paystack
processes the charge, then the response is lost to a partition, and the
timeout tells the caller nothing about which happened. Retry blindly and
you double-charge; don't retry and the payment stays unresolved. That
asymmetry — the system consistent but the caller's knowledge wrong — is
why ambiguity, not crashes, is the first-class object of the study.

## 12. "Why MCP rather than a standalone tool or script?"

Portability and fairness. One server serves any compliant agent, so the
evaluation across three agents tests one intervention, not three
integrations. And the protocol is honest about its limits: it carries
calls, not obligations — nothing compels invocation, which is why the
study instructs tool use explicitly and names protocol-level enforcement
as future work.
