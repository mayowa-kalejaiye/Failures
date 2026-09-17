import os
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
PRINCIPLES_DIR = DOCS_DIR / "principles"

PRINCIPLES_DIR.mkdir(parents=True, exist_ok=True)
LABS_DIR = DOCS_DIR / "labs"

# Authentic Failures SVG Logo (with prominent red failure badge)
FAILURES_LOGO = """<svg width="20" height="20" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="32" height="32" rx="7" fill="currentColor" fill-opacity="0.12"/>
  <path d="M10 8 H22 M10 15 H18 M10 8 V24" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="23" cy="23" r="6.5" fill="#ef4444"/>
  <path d="M20.5 20.5l5 5M25.5 20.5l-5 5" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
</svg>"""

# Official Tech & Company SVGs — authentic brand icons
COMPANY_LOGOS = {
    "openai": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M22.282 9.821a6 6 0 0 0-.516-4.91a6.05 6.05 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a6 6 0 0 0-3.998 2.9a6.05 6.05 0 0 0 .743 7.097a5.98 5.98 0 0 0 .51 4.911a6.05 6.05 0 0 0 6.515 2.9A6 6 0 0 0 13.26 24a6.06 6.06 0 0 0 5.772-4.206a6 6 0 0 0 3.997-2.9a6.06 6.06 0 0 0-.747-7.073M13.26 22.43a4.48 4.48 0 0 1-2.876-1.04l.141-.081l4.779-2.758a.8.8 0 0 0 .392-.681v-6.737l2.02 1.168a.07.07 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494M3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085l4.783 2.759a.77.77 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646M2.34 7.896a4.5 4.5 0 0 1 2.366-1.973V11.6a.77.77 0 0 0 .388.677l5.815 3.354l-2.02 1.168a.08.08 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.08.08 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667m2.01-3.023l-.141-.085l-4.774-2.782a.78.78 0 0 0-.785 0L9.409 9.23V6.897a.07.07 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.8.8 0 0 0-.393.681zm1.097-2.365l2.602-1.5l2.607 1.5v2.999l-2.597 1.5l-2.607-1.5Z"/></svg>""",
    # Anthropic Claude — real starburst mark from Simple Icons
    "claude": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>""",
    # Cursor — angled cursor pointer with secondary sparkle stroke
    "cursor": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 2.5a.75.75 0 0 0-1.05 1.02l9 9-3.5 1.45a.75.75 0 0 0 .3 1.42l10 4a.75.75 0 0 0 .95-.96V4.75a.75.75 0 0 0-.95-.72L4.5 2.5z"/></svg>""",
    # Cline — terminal bracket style (real Cline icon approach)
    "cline": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>""",
    # Windsurf (Codeium) — wave/surf arcs, their actual brand shape
    "windsurf": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 19c2-4 5-6 8-6s6 2 8 6"/><path d="M5 13c1.5-3.5 4-5.5 7-5.5s5.5 2 7 5.5"/><path d="M9 7.5c1-3 2.5-4.5 3-4.5s2 1.5 3 4.5"/></svg>""",
    # Devin (Cognition AI) — square robot/agent face
    "devin": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="10" r="1.5" fill="currentColor"/><circle cx="15" cy="10" r="1.5" fill="currentColor"/><path d="M9 15h6"/></svg>""",
    # GitHub Copilot — real copilot logo paths
    "copilot": """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M9.75 14.25c0 .414-.336.75-.75.75s-.75-.336-.75-.75.336-.75.75-.75.75.336.75.75zm6 0c0 .414-.336.75-.75.75s-.75-.336-.75-.75.336-.75.75-.75.75.336.75.75zM12 2C6.477 2 2 6.477 2 12c0 4.236 2.636 7.855 6.356 9.312-.09-.696-.173-1.764.036-2.524.189-.693.99-4.204 1.43-6.038-.37-.733-.37-2.454.762-2.454.88 0 1.213.765 1.213 1.474 0 1.008-.643 2.517-.643 2.517.366 1.581 1.757 2.107 2.794 2.107 2.036 0 3.394-2.15 3.394-5.027C19.342 9.26 17.19 7.5 14.15 7.5c-3.534 0-5.613 2.65-5.613 5.397 0 1.069.406 2.213 1.013 2.839.112.117.128.22.095.34-.1.427-.331 1.34-.38 1.527-.06.24-.201.29-.462.174-1.727-.8-2.807-3.318-2.807-5.338C6.996 9.028 9.548 6 14.2 6 17.87 6 20.75 8.56 20.75 12.2c0 3.927-2.437 6.8-5.8 6.8-1.14 0-2.21-.59-2.58-1.286l-.704 2.63c-.252.99-.935 2.232-1.393 2.988C11 23.954 11.493 24 12 24c6.627 0 12-5.373 12-12S18.627 2 12 2z"/></svg>""",
    "postgres": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>""",
    "redis": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>""",
    "stripe": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697.5 12.608.5 6.775.5 2.87 3.513 2.87 8.35c0 4.908 3.794 6.724 7.643 8.163 2.502.932 3.356 1.656 3.356 2.651 0 .995-.875 1.543-2.34 1.543-2.497 0-5.385-1.127-7.234-2.224l-.94 5.48c1.944 1.05 5.064 1.737 8.318 1.737 6.136 0 10.228-2.906 10.228-8.082 0-4.708-3.447-6.524-7.925-8.468z"/></svg>""",
    "supabase": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M21.362 9.354H12V.396a.396.396 0 0 0-.716-.233L.32 14.242a.396.396 0 0 0 .307.637H12v8.725a.396.396 0 0 0 .716.233l10.964-14.079a.396.396 0 0 0-.318-.404z"/></svg>""",
    "resend": """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h18v18H3V3zm15 15V6H6v12h12z"/></svg>""",
    "github": """<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>"""
}

# 11 Core Principles Data
PRINCIPLES = [
    {
        "id": "atomicity",
        "num": "01",
        "name": "Atomicity",
        "question": "Can an operation partially succeed?",
        "invariant": "Operation must fully succeed or fully fail; no intermediate state visible.",
        "severity": "CRITICAL",
        "dot": "critical",
        "applies_to": ["payments", "orders", "enrollments", "inventory", "database writes", "queues with side effects"],
        "failure_modes": ["partial_commit", "crash_between_writes", "orphaned_side_effect"],
        "patterns": ["transactional-outbox", "saga"],
        "tests": ["crash_between_writes", "db_failure_after_provider_success"],
        "desc": "A first-principles walkthrough of why an operation must be all-or-nothing, what a commit actually does underneath (WAL, fsync, visibility), why a crash between a Stripe charge and an INSERT leaves money taken with no record, and how a pending row plus transactional outbox restores atomicity across services. Grounded in Postgres transactions and the dual-write problem.",
        "code_bad": """# NAIVE: Process crash leaves customer charged without order record
async def process_checkout(user_id: str, amount: float):
    charge = await stripe.charge(amount=amount)
    await db.execute("INSERT INTO orders (user_id, status) VALUES (%s, 'paid')", user_id)
    return {"order_id": charge.id}""",
        "code_good": """# IMPROVED: Transactional outbox & pending state before charge
async def process_checkout(user_id: str, amount: float, idempotency_key: str):
    async with db.transaction() as tx:
        order = await tx.execute(
            "INSERT INTO orders (id, user_id, amount, status, idempotency_key) "
            "VALUES (%s, %s, %s, 'pending', %s) RETURNING id",
            uuid4(), user_id, amount, idempotency_key
        )
    try:
        charge = await stripe.charge(amount=amount, idempotency_key=idempotency_key)
        await db.execute("UPDATE orders SET status = 'confirmed', charge_id = %s WHERE id = %s", charge.id, order.id)
    except Exception as e:
        logger.error(f"Checkout error for order {order.id}: {e}")
        raise""",
        "code_bad_js": """// NAIVE: Process crash leaves customer charged without order record
async function processCheckout(userId, amount) {
  const charge = await stripe.charges.create({ amount });
  await db.query('INSERT INTO orders (user_id, status) VALUES ($1, \'paid\')', [userId]);
  return { orderId: charge.id };
}""",
        "code_good_js": """// IMPROVED: Transactional outbox & pending state before charge
async function processCheckout(userId, amount, idempotencyKey) {
  const order = await db.query(
    'INSERT INTO orders (id, user_id, amount, status, idempotency_key) VALUES ($1,$2,$3,\'pending\',$4) RETURNING id',
    [crypto.randomUUID(), userId, amount, idempotencyKey]
  );
  try {
    const charge = await stripe.charges.create({ amount }, { idempotencyKey });
    await db.query('UPDATE orders SET status = \'confirmed\', charge_id = $1 WHERE id = $2', [charge.id, order.rows[0].id]);
  } catch (e) {
    console.error(`Checkout error for order ${order.rows[0].id}:`, e);
    throw e;
  }
}"""
    },
    {
        "id": "idempotency",
        "num": "02",
        "name": "Idempotency",
        "question": "What happens if the same operation happens twice?",
        "invariant": "One logical operation produces at most one effect regardless of executions.",
        "severity": "CRITICAL",
        "dot": "critical",
        "applies_to": ["payments", "webhooks", "queues", "mutating POSTs", "external APIs", "enrollments"],
        "failure_modes": ["duplicate_side_effect", "duplicate_record", "double_charge"],
        "patterns": ["idempotency-key"],
        "tests": ["retry_after_timeout", "duplicate_request", "duplicate_idempotency_key"],
        "desc": "A first-principles walkthrough of why the network makes every request potentially twice — timeout, retry, redelivery — what “the same operation” means as business policy (same key vs same key+amount), and how a persisted idempotency key with a UNIQUE constraint turns a non-idempotent POST into a safe retry. The key must be written before the side effect, not after.",
        "code_bad": """# NAIVE: Retrying this endpoint charges the card multiple times
@app.post("/api/enroll")
async def enroll_student(payload: EnrollRequest):
    res = await payment_gateway.charge(payload.amount)
    await db.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", payload.student_id, payload.course_id)
    return {"status": "enrolled"}""",
        "code_good": """# IMPROVED: Idempotency table + unique constraint
@app.post("/api/enroll")
async def enroll_student(payload: EnrollRequest, idem_key: str = Header(None)):
    if not idem_key:
        raise HTTPException(400, "Idempotency-Key header required")
    existing = await db.fetch_one("SELECT response, status FROM idempotency_keys WHERE key = %s", idem_key)
    if existing:
        if existing['status'] == 'completed':
            return json.loads(existing['response'])
        elif existing['status'] == 'pending':
            raise HTTPException(409, "Operation currently processing in flight")
    await db.execute("INSERT INTO idempotency_keys (key, status) VALUES (%s, 'pending')", idem_key)
    try:
        charge = await payment_gateway.charge(payload.amount, idempotency_key=idem_key)
        await db.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", payload.student_id, payload.course_id)
        resp = {"status": "enrolled", "charge_id": charge.id}
        await db.execute("UPDATE idempotency_keys SET status = 'completed', response = %s WHERE key = %s", json.dumps(resp), idem_key)
        return resp
    except Exception as e:
        await db.execute("DELETE FROM idempotency_keys WHERE key = %s", idem_key)
        raise""",
        "code_bad_js": """// NAIVE: Retrying this endpoint charges the card multiple times
app.post('/api/enroll', async (req, res) => {
  const charge = await paymentGateway.charge(req.body.amount);
  await db.query('INSERT INTO enrollments (student_id, course_id) VALUES ($1,$2)', [req.body.studentId, req.body.courseId]);
  res.json({ status: 'enrolled' });
});""",
        "code_good_js": """// IMPROVED: Idempotency table + unique constraint
app.post('/api/enroll', async (req, res) => {
  const key = req.headers['idempotency-key'];
  if (!key) return res.status(400).json({ error: 'Idempotency-Key required' });
  const existing = await db.query('SELECT response, status FROM idempotency_keys WHERE key = $1', [key]);
  if (existing.rows[0]) {
    if (existing.rows[0].status === 'completed') return res.json(JSON.parse(existing.rows[0].response));
    if (existing.rows[0].status === 'pending') return res.status(409).json({ error: 'Operation in flight' });
  }
  await db.query('INSERT INTO idempotency_keys (key, status) VALUES ($1, \'pending\')', [key]);
  try {
    const charge = await paymentGateway.charge(req.body.amount, { idempotencyKey: key });
    await db.query('INSERT INTO enrollments (student_id, course_id) VALUES ($1,$2) ON CONFLICT DO NOTHING', [req.body.studentId, req.body.courseId]);
    const resp = { status: 'enrolled', chargeId: charge.id };
    await db.query('UPDATE idempotency_keys SET status = \'completed\', response = $1 WHERE key = $2', [JSON.stringify(resp), key]);
    res.json(resp);
  } catch (e) {
    await db.query('DELETE FROM idempotency_keys WHERE key = $1', [key]);
    throw e;
  }
});"""
    },
    {
        "id": "timeout",
        "num": "03",
        "name": "Timeout / Ambiguous Outcome",
        "question": "Timeout does not equal failure. Did it succeed?",
        "invariant": "System must handle ambiguous outcomes without duplicate side effects.",
        "severity": "CRITICAL",
        "dot": "critical",
        "applies_to": ["external APIs", "payment providers", "databases", "queues"],
        "failure_modes": ["ambiguous_success", "success_then_timeout", "retry_after_ambiguous"],
        "patterns": ["idempotency-key", "reconciliation"],
        "tests": ["retry_after_provider_success", "dependency_timeout"],
        "desc": "A first-principles walkthrough of why a timeout tells you nothing about success. TCP hid whether the bytes arrived, HTTP hid whether the handler ran. Every timeout is ambiguous by design, so we never treat it as failure: persist pending before calling, then reconcile with the provider as the source of truth, never blindly retry a non-idempotent charge.",
        "code_bad": """# NAIVE: Treating timeout as failure
async def pay_invoice(invoice_id: str, amount: float):
    try: return await http_client.post("/charge", json={"amount": amount}, timeout=10.0)
    except TimeoutException: return await http_client.post("/charge", json={"amount": amount})""",
        "code_good": """# IMPROVED: Handling timeout as AMBIGUOUS
async def pay_invoice(invoice_id: str, amount: float):
    op_id = f"inv_{invoice_id}_{uuid4()}"
    try:
        res = await http_client.post("/charge", json={"amount": amount}, headers={"Idempotency-Key": op_id}, timeout=10.0)
        return res.json()
    except (TimeoutException, httpx.NetworkError):
        status = await reconcile_with_provider(op_id)
        if status.is_confirmed: return status.data
        raise OperationPendingException("Payment pending confirmation")""",
        "code_bad_js": """// NAIVE: Treating timeout as failure
async function payInvoice(invoiceId, amount) {
  try { return await http.post('/charge', { amount }, { timeout: 10000 }); }
  catch (e) { if (e.code === 'ETIMEDOUT') return await http.post('/charge', { amount }); throw e; }
}""",
        "code_good_js": """// IMPROVED: Handling timeout as AMBIGUOUS
async function payInvoice(invoiceId, amount) {
  const opId = `inv_${invoiceId}_${crypto.randomUUID()}`;
  try {
    const res = await http.post('/charge', { amount }, { headers: { 'Idempotency-Key': opId }, timeout: 10000 });
    return res.data;
  } catch (e) {
    if (e.code === 'ETIMEDOUT' || e.code === 'ECONNRESET') {
      const status = await reconcileWithProvider(opId);
      if (status.isConfirmed) return status.data;
      throw new OperationPendingError('Payment pending confirmation');
    }
    throw e;
  }
}"""
    },
    {
        "id": "concurrency",
        "num": "04",
        "name": "Concurrency",
        "question": "What if two actors modify the same state?",
        "invariant": "Concurrent modifications must not cause lost updates or double effects.",
        "severity": "HIGH",
        "dot": "high",
        "applies_to": ["inventory", "balances", "enrollments", "token refresh", "counters"],
        "failure_modes": ["lost_update", "double_enrollment", "race_on_write"],
        "patterns": ["optimistic-locking", "pessimistic-locking"],
        "tests": ["concurrent_update"],
        "desc": "A first-principles walkthrough of what happens when two actors read the same row at the same instant. The lost-update — both read seats=1, both write 0, one sale disappears. Why read-modify-write is never safe without a lock, and how SELECT FOR UPDATE and versioned optimistic locking make the check atomic at the database, not in application memory.",
        "code_bad": """# NAIVE: Read-modify-write race condition
async def purchase_ticket(event_id: str):
    event = await db.fetch_one("SELECT seats_left FROM events WHERE id = %s", event_id)
    if event['seats_left'] > 0:
        await db.execute("UPDATE events SET seats_left = %s WHERE id = %s", event['seats_left'] - 1, event_id)
        return True
    return False""",
        "code_good": """# IMPROVED: Optimistic locking with atomic condition
async def purchase_ticket(event_id: str):
    res = await db.execute("UPDATE events SET seats_left = seats_left - 1, version = version + 1 WHERE id = %s AND seats_left > 0", event_id)
    if res.rows_affected == 0:
        raise HTTPException(409, "No seats available or concurrent conflict")
    return {"status": "confirmed"}""",
        "code_bad_js": """// NAIVE: Read-modify-write race condition
async function purchaseTicket(eventId) {
  const event = await db.query('SELECT seats_left FROM events WHERE id = $1', [eventId]);
  if (event.rows[0].seats_left > 0) {
    await db.query('UPDATE events SET seats_left = $1 WHERE id = $2', [event.rows[0].seats_left - 1, eventId]);
    return true;
  }
  return false;
}""",
        "code_good_js": """// IMPROVED: Optimistic locking with atomic condition
async function purchaseTicket(eventId) {
  const res = await db.query('UPDATE events SET seats_left = seats_left - 1, version = version + 1 WHERE id = $1 AND seats_left > 0', [eventId]);
  if (res.rowCount === 0) throw Object.assign(new Error('No seats or conflict'), { status: 409 });
  return { status: 'confirmed' };
}"""
    },
    {
        "id": "retry-safety",
        "num": "05",
        "name": "Retry Safety",
        "question": "Is it safe to retry? What retries are allowed?",
        "invariant": "Retries must be safe, bounded, with backoff and idempotency.",
        "severity": "HIGH",
        "dot": "high",
        "applies_to": ["external calls", "webhooks", "queue consumers"],
        "failure_modes": ["retry_storm", "thundering_herd", "duplicate_on_retry"],
        "patterns": ["circuit-breaker"],
        "tests": ["retry_storm", "retry_after_503"],
        "desc": "A first-principles walkthrough of why retries are inevitable in any distributed system and why an unbounded retry loop is a distributed amplifier. How a tight loop on a 500 turns a single slow dependency into a thundering herd, and how exponential backoff with jitter, a retry budget, and the rule “only retry idempotent operations” make retries safe, bounded, and backpressure-aware.",
        "code_bad": """# NAIVE: Tight retry loop
async def send_sms(user_id: str, msg: str):
    for _ in range(10):
        try: return await sms.send(user_id, msg)
        except: time.sleep(0.1)
    raise FailedException()""",
        "code_good": """# IMPROVED: Exponential backoff with full jitter
async def send_sms(user_id: str, msg: str, key: str):
    for attempt in range(1, 5):
        try: return await sms.send(user_id, msg, idempotency_key=f"{key}_{attempt}")
        except RetriableException:
            delay = random.uniform(0, min(8.0, 0.5 * (2 ** (attempt - 1))))
            await asyncio.sleep(delay)
    raise FailedException()""",
        "code_bad_js": """// NAIVE: Tight retry loop
async function sendSms(userId, msg) {
  for (let i = 0; i < 10; i++) {
    try { return await sms.send(userId, msg); }
    catch (e) { await new Promise(r => setTimeout(r, 100)); }
  }
  throw new Error('Failed');
}""",
        "code_good_js": """// IMPROVED: Exponential backoff with full jitter
async function sendSms(userId, msg, key) {
  for (let attempt = 1; attempt <= 4; attempt++) {
    try { return await sms.send(userId, msg, { idempotencyKey: `${key}_${attempt}` }); }
    catch (e) {
      if (!isRetriable(e)) throw e;
      const delay = Math.random() * Math.min(8000, 500 * (2 ** (attempt - 1)));
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Failed');
}"""
    },
    {
        "id": "availability",
        "num": "06",
        "name": "Availability",
        "question": "What happens when a dependency disappears?",
        "invariant": "Failure of one dependency must not cascade to full outage.",
        "severity": "HIGH",
        "dot": "high",
        "applies_to": ["databases", "payment providers", "queues", "caches", "external services"],
        "failure_modes": ["cascade", "pool_exhaustion", "hanging_workers"],
        "patterns": ["circuit-breaker"],
        "tests": ["dependency_unavailable", "downstream_hang"],
        "desc": "A first-principles walkthrough of why a hung dependency can take down your entire fleet. How a thread pool exhausts while waiting on a slow Recs API, why a timeout alone is not enough, and how a circuit breaker (closed→open→half-open) plus bulkheads and fallbacks isolate the failure and fail fast instead of cascading.",
        "code_bad": """# NAIVE: Unprotected call blocks thread indefinitely
@app.get("/user/dashboard")
async def get_dashboard(user_id: str):
    recs = await http_client.get(f"https://recs.internal/v1/{user_id}")
    return {"recs": recs.json()}""",
        "code_good": """# IMPROVED: Circuit breaker + fallback
@app.get("/user/dashboard")
async def get_dashboard(user_id: str):
    if breaker.is_open(): return {"recs": await get_default_recs()}
    try:
        res = await http_client.get(f"https://recs.internal/v1/{user_id}", timeout=1.5)
        breaker.record_success()
        return {"recs": res.json()}
    except Exception:
        breaker.record_failure()
        return {"recs": await get_default_recs()}""",
        "code_bad_js": """// NAIVE: Unprotected call blocks thread indefinitely
app.get('/user/dashboard', async (req, res) => {
  const recs = await fetch(`https://recs.internal/v1/${req.query.userId}`);
  res.json({ recs: await recs.json() });
});""",
        "code_good_js": """// IMPROVED: Circuit breaker + fallback
app.get('/user/dashboard', async (req, res) => {
  if (breaker.isOpen()) return res.json({ recs: await getDefaultRecs() });
  try {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 1500);
    const r = await fetch(`https://recs.internal/v1/${req.query.userId}`, { signal: controller.signal });
    clearTimeout(t);
    breaker.recordSuccess();
    res.json({ recs: await r.json() });
  } catch (e) {
    breaker.recordFailure();
    res.json({ recs: await getDefaultRecs() });
  }
});"""
    },
    {
        "id": "ordering",
        "num": "07",
        "name": "Ordering",
        "question": "What if events arrive out of order?",
        "invariant": "System must tolerate or enforce ordering where correctness depends on it.",
        "severity": "HIGH",
        "dot": "high",
        "applies_to": ["queues", "webhooks", "event streams", "enrollments"],
        "failure_modes": ["out_of_order", "stale_overwrites_fresh"],
        "patterns": ["sequence-numbering"],
        "tests": ["out_of_order_events"],
        "desc": "A first-principles walkthrough of why queues and webhooks cannot promise order. A delayed “created” delivery can arrive after “cancelled” and wrongly re-activate a subscription. Why sequence numbers and monotonic timestamp guards (WHERE last_ts < incoming) make stale deliveries harmless without global ordering.",
        "code_bad": """# NAIVE: Overwriting status blindly on webhook delivery
@app.post("/webhooks/sub")
async def handle_sub(event: Event):
    await db.execute("UPDATE subs SET status = %s WHERE id = %s", event.status, event.sub_id)""",
        "code_good": """# IMPROVED: Monotonic timestamp sequence check
@app.post("/webhooks/sub")
async def handle_sub(event: Event):
    await db.execute("UPDATE subs SET status = %s, last_ts = %s WHERE id = %s AND last_ts < %s", event.status, event.ts, event.sub_id, event.ts)""",
        "code_bad_js": """// NAIVE: Overwriting status blindly on webhook delivery
app.post('/webhooks/sub', async (req, res) => {
  await db.query('UPDATE subs SET status = $1 WHERE id = $2', [req.body.status, req.body.sub_id]);
  res.sendStatus(200);
});""",
        "code_good_js": """// IMPROVED: Monotonic timestamp sequence check
app.post('/webhooks/sub', async (req, res) => {
  await db.query('UPDATE subs SET status = $1, last_ts = $2 WHERE id = $3 AND last_ts < $2', [req.body.status, req.body.ts, req.body.sub_id]);
  res.sendStatus(200);
});"""
    },
    {
        "id": "consistency",
        "num": "08",
        "name": "Consistency",
        "question": "What happens when replicas/caches disagree?",
        "invariant": "Readers must not act on stale conflicting state.",
        "severity": "MEDIUM",
        "dot": "medium",
        "applies_to": ["caches", "read replicas", "sessions"],
        "failure_modes": ["stale_read", "revoked_session_still_valid"],
        "patterns": ["cache-invalidation"],
        "tests": ["stale_cache_read"],
        "desc": "A first-principles walkthrough of why replicas and caches necessarily disagree for a window. What read-your-writes, linearizable reads, and replication lag cost in latency, and how write-through invalidation and version checks close the gap between the primary and what the reader sees.",
        "code_bad": """# NAIVE: Revoking token in DB without cache invalidation
async def revoke(session_id: str):
    await db.execute("UPDATE sessions SET revoked = TRUE WHERE id = %s", session_id)""",
        "code_good": """# IMPROVED: Write-through cache invalidation
async def revoke(session_id: str):
    async with db.transaction():
        await db.execute("UPDATE sessions SET revoked = TRUE WHERE id = %s", session_id)
        await redis.delete(f"session:{session_id}")""",
        "code_bad_js": """// NAIVE: Revoking token in DB without cache invalidation
async function revoke(sessionId) {
  await db.query('UPDATE sessions SET revoked = TRUE WHERE id = $1', [sessionId]);
}""",
        "code_good_js": """// IMPROVED: Write-through cache invalidation
async function revoke(sessionId) {
  await db.query('BEGIN');
  await db.query('UPDATE sessions SET revoked = TRUE WHERE id = $1', [sessionId]);
  await redis.del(`session:${sessionId}`);
  await db.query('COMMIT');
}"""
    },
    {
        "id": "resource-exhaustion",
        "num": "09",
        "name": "Resource Exhaustion",
        "question": "What happens when capacity is exceeded?",
        "invariant": "System must bound resource use and shed load gracefully.",
        "severity": "HIGH",
        "dot": "high",
        "applies_to": ["APIs", "connection pools", "queues", "file uploads"],
        "failure_modes": ["pool_exhaustion", "oom_on_large_file", "burst_overload"],
        "patterns": ["rate-limiting", "bulkhead"],
        "tests": ["burst_rate_limit"],
        "desc": "A first-principles walkthrough of why unbounded work always finds a limit — connection pools, memory, queue depth, file size. How an unbounded `await file.read()` OOMs the process, and how bounded pools, token-bucket rate limiting, chunked streaming, and backpressure shed load gracefully instead of crashing.",
        "code_bad": """# NAIVE: Reading full file into RAM
@app.post("/upload")
async def upload(file: UploadFile):
    return {"size": len(await file.read())}""",
        "code_good": """# IMPROVED: Chunked streaming with size caps
@app.post("/upload")
async def upload(file: UploadFile):
    while chunk := await file.read(64 * 1024):
        await stream_save(chunk)""",
        "code_bad_js": """// NAIVE: Reading full file into RAM
app.post('/upload', async (req, res) => {
  const buf = await req.file.arrayBuffer();
  res.json({ size: buf.byteLength });
});""",
        "code_good_js": """// IMPROVED: Chunked streaming with size caps
import { pipeline } from 'node:stream/promises';
app.post('/upload', async (req, res) => {
  for await (const chunk of req.file.stream()) {
    await streamSave(chunk); // 64KB chunks, backpressure handled
  }
  res.json({ ok: true });
});"""
    },
    {
        "id": "recovery",
        "num": "10",
        "name": "Recovery",
        "question": "How does system return to valid state?",
        "invariant": "Every failure has a recovery path to a valid state.",
        "severity": "MEDIUM",
        "dot": "medium",
        "applies_to": ["queues", "payments", "enrollments", "file uploads"],
        "failure_modes": ["poison_message", "redelivery_without_idempotency", "pending_forever"],
        "patterns": ["dead-letter-queue", "reconciliation"],
        "tests": ["crash_before_ack", "queue_duplicate_delivery", "poison_message"],
        "desc": "A first-principles walkthrough of how a system returns to a valid state after a poison message or a crash before ack. Why an at-least-once queue without an idempotent consumer stays broken, and how a dead-letter queue plus a reconciliation sweeper are the two recovery paths that prevent pending-forever.",
        "code_bad": """# NAIVE: Poison message crashes consumer
async def consume():
    msg = await q.pop()
    data = json.loads(msg.body)
    await q.ack(msg)""",
        "code_good": """# IMPROVED: Dead Letter Queue routing on failure
async def consume():
    msg = await q.pop()
    try:
        data = json.loads(msg.body)
        await q.ack(msg)
    except Exception as e:
        await dlq.push(msg, error=str(e))
        await q.ack(msg)""",
        "code_bad_js": """// NAIVE: Poison message crashes consumer
async function consume() {
  const msg = await queue.pop();
  const data = JSON.parse(msg.body);
  await queue.ack(msg);
}""",
        "code_good_js": """// IMPROVED: Dead Letter Queue routing on failure
async function consume() {
  const msg = await queue.pop();
  try {
    const data = JSON.parse(msg.body);
    await queue.ack(msg);
  } catch (e) {
    await dlq.push(msg, { error: String(e) });
    await queue.ack(msg);
  }
}"""
    },
    {
        "id": "observability",
        "num": "11",
        "name": "Observability",
        "question": "How do we know what actually happened?",
        "invariant": "Every operation must be traceable to its outcome.",
        "severity": "MEDIUM",
        "dot": "medium",
        "applies_to": ["all components"],
        "failure_modes": ["untraceable_failure", "missing_audit_trail"],
        "patterns": ["structured-logging"],
        "tests": ["reconstruct_from_logs"],
        "desc": "A first-principles walkthrough of how you reconstruct what actually happened after a failure. Why a print statement is not observability, how a correlation ID must be carried across every hop, and how structured JSON logs with operation IDs make the timeline queryable in Loki/Datadog after a crash.",
        "code_bad": """# NAIVE: Generic print statements
print(f"transfer {amt}")""",
        "code_good": """# IMPROVED: Structured logging with trace ID
log.info("transfer.completed", trace_id=trace_id, amount=amt, duration_ms=12.4)""",
        "code_bad_js": """// NAIVE: Generic print statements
console.log(`transfer ${amt}`);""",
        "code_good_js": """// IMPROVED: Structured logging with trace ID
logger.info('transfer.completed', { traceId, amount: amt, durationMs: 12.4 });"""
    }
]

# Verbose first-principles bodies for docs — very verbose, like Backend from First Principles
PRINCIPLE_VERBOSE = {
    "atomicity": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Every database write is not a single action but a sequence: the client sends a query, the engine appends to the Write-Ahead Log (WAL), fsyncs to disk, updates the heap page, and only then reports success. A transaction groups several of these sequences into one all-or-nothing gate. <code>BEGIN</code> opens the gate, <code>COMMIT</code> closes it and makes all WAL entries visible at once, <code>ROLLBACK</code> discards them. Without that gate, a process crash between two <code>INSERT</code>s leaves the first visible and the second absent — a partial commit.</p>
    <p>Think of a bank transfer as two letters that must arrive together: debit and credit. If the courier crashes after delivering only the debit, money vanishes. The transaction is the envelope that says “deliver both or deliver neither.” Distributed systems cannot envelope two services in one gate, so we use the <strong>transactional outbox</strong>: persist the order and an <code>outbox</code> event in the same local transaction, then a relay publishes the event. The outbox is the envelope.</p>
    <div class="my-4 p-3 border border-dashed border-foreground/[0.08] bg-foreground/[0.02] font-mono text-[11px] leading-relaxed">
    Client → BEGIN → INSERT pending order → INSERT outbox → COMMIT → (then) Stripe charge → UPDATE confirmed<br>
    Crash between charge and UPDATE? Row stays <code>pending</code>, reconciler re-checks provider as source of truth.
    </div>
    <h2 id="misconceptions">Common Misconceptions</h2>
    <p><strong>“I wrapped it in a try/catch, so it’s atomic.”</strong> A catch does not undo a committed row. Only a transaction does. Another: “A single HTTP request is atomic.” A request that does two writes is two chances to crash, not one.</p>
    <h2 id="detection">How to Detect It</h2>
    <p>Search for any handler that does more than one <code>db.execute</code> without an explicit <code>BEGIN</code>/<code>transaction()</code>. In code review, ask: “If the process dies between line N and N+1, what row is visible?” The answer must be “none.”</p>
    """ ,
    "idempotency": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>The network has amnesia: a client that times out after 5 seconds cannot know whether the server received the bytes, processed them, or never saw them. TCP hid the loss, HTTP hides the handler state. The only way to make “send again” safe is to give the *logical* operation a name that survives retries. That name is the idempotency key — a UUID generated by the client for one checkout attempt, not per HTTP attempt. The server stores <code>key → result</code> durably (database table with <code>UNIQUE(key)</code>, not an in-memory map) before doing work, and on a repeat key returns the stored result without re-executing. The key turns a non-idempotent POST into “at most once.”</p>
    <p>Analogy: a postal office that stamps every letter with a tracking number. If the same tracking number arrives twice, the office does not deliver two parcels — it returns the delivery receipt of the first.</p>
    <div class="my-4 p-3 border border-dashed border-foreground/[0.08] bg-foreground/[0.02] font-mono text-[11px] leading-relaxed">
    Client: POST /pay + Idempotency-Key: 9f8c… (same key on retry)<br>
    Server: SELECT key → miss → INSERT pending → charge(provider, same key) → UPDATE completed + response → return<br>
    Retry with same key → SELECT hit → return cached response, no second charge.
    </div>
    <h2 id="misconceptions">Common Misconceptions</h2>
    <p><strong>“The provider’s idempotency is enough.”</strong> Stripe’s key protects Stripe, not your local <code>INSERT enrollment</code> that follows it. You need a local key that guards the whole operation. Another: “A random UUID per retry is fine.” A new UUID per retry is a new logical operation — it guarantees duplication.</p>
    <h2 id="detection">How to Detect It</h2>
    <p>Any mutating <code>POST</code> or queue consumer that can be retried and lacks a <code>SELECT ... WHERE key = ?</code> before the side effect is suspect. Ask: “If the client retries with the same key, do we have a UNIQUE to catch it and a cached response to return?”</p>
    """ ,
    "timeout": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Timeout is a client-side decision to stop waiting. It tells you nothing about the server: the server may have succeeded a millisecond after you gave up, may be still running, or may never have received the request. This is the <em>ambiguous outcome</em> — the most dangerous failure class. TCP already hid whether the bytes arrived; HTTP hides whether the handler committed. Treating timeout as failure and blindly retrying a non-idempotent charge is how double debits happen.</p>
    <p>The correct machinery is: never retry without an idempotency key, persist a <code>pending</code> state before calling, and on timeout do not guess — <em>reconcile</em>. The reconciler asks the provider “what is the truth for reference X?” and drives the local row to <code>completed</code> or <code>failed</code>. The provider, not the timeout, is the source of truth.</p>
    <div class="my-4 p-3 border border-dashed border-foreground/[0.08] bg-foreground/[0.02] font-mono text-[11px] leading-relaxed">
    try: POST /charge Idempotency-Key: op_123 timeout=5s → Timeout<br>
    not: retry POST → instead: GET /charge/op_123 (reconcile) → if confirmed return, else mark pending for sweeper
    </div>
    <h2 id="misconceptions">Common Misconceptions</h2>
    <p><strong>“Timeout means it failed.”</strong> No — it means “I don’t know.” Another: “A longer timeout fixes it.” A longer wait just moves the ambiguity window, it does not remove it.</p>
    <h2 id="detection">How to Detect It</h2>
    <p>Every outgoing HTTP call must have an explicit <code>timeout=</code>. Search for <code>requests.post</code> or <code>httpx</code> without <code>timeout</code> — that worker will hang forever and its pool will exhaust.</p>
    """ ,
    "concurrency": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Concurrency is two actors reading the same row at the same instant. Each reads <code>seats=1</code>, each checks <code>if seats>0</code>, each writes <code>seats=0</code>. One sale consumed two seats, one customer is oversold, and no error was thrown. The database executed both writes correctly — the bug is that the <em>check</em> and the <em>write</em> were not atomic. The fix is to make the check part of the write: <code>UPDATE seats SET seats=seats-1 WHERE seats>0</code> and inspect <code>rows_affected</code>, or <code>SELECT ... FOR UPDATE</code> to lock the row between read and write, or a version column with <code>WHERE version=expected</code>.</p>
    <div class="my-4 p-3 border border-dashed border-foreground/[0.08] bg-foreground/[0.02] font-mono text-[11px] leading-relaxed">
    T1: READ seats=1 ─┐<br>
    T2: READ seats=1 ─┼─ both see 1, both write 0 → lost update<br>
    Fix: UPDATE ... WHERE seats>0 → second UPDATE affects 0 rows → 409
    </div>
    <h2 id="misconceptions">Common Misconceptions</h2>
    <p><strong>“My language is single-threaded, so no race.”</strong> Concurrency is not threads — it is two HTTP requests from two users hitting two server processes at the same millisecond. The race is in the database, not in your runtime.</p>
    """ ,
    "retry-safety": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Retries are inevitable: the network drops, the provider 503s, the user double-clicks. An unbounded retry loop is a distributed amplifier. One slow dependency that returns 500 for 2 seconds, retried immediately by 100 clients, becomes 100× load at the exact moment the dependency is weakest. The fix is three parts: only retry what is idempotent, wait with exponential backoff and jitter so retries spread, and bound the total with a retry budget and a circuit breaker that trips to open after N failures and fails fast without hammering.</p>
    <div class="my-4 p-3 border border-dashed border-foreground/[0.08] bg-foreground/[0.02] font-mono text-[11px] leading-relaxed">
    attempt 1 → 429 → wait 1s + jitter → attempt 2 → 429 → wait 2s → attempt 3 → 200<br>
    Without jitter: 100 clients retry at 1.0s, 2.0s — thundering herd. With jitter: retries scatter.
    </div>
    <h2 id="misconceptions">Common Misconceptions</h2>
    <p><strong>“More retries = more reliability.”</strong> More retries without backoff is a self-inflicted DDoS. Another: “Retry on 400.” 400 is the client’s fault — retrying never fixes a bad request.</p>
    """ ,
    "availability": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Availability is not “the dependency is up.” It is “your system stays up when the dependency is down.” A single <code>await http.get("https://recs.internal")</code> without a timeout holds a worker thread for 30 seconds. Ten concurrent dashboard loads hold ten workers. The pool exhausts, health checks fail, the load balancer marks the node dead, and the outage cascades. The machinery is timeout (bound the wait), circuit breaker (count failures, trip to open, return fallback without calling), and bulkhead (isolate pools so one slow dependency cannot steal all workers).</p>
    <h2 id="detection">How to Detect It</h2>
    <p>Search for any <code>await http</code> without <code>timeout=</code> and without a breaker wrapper. If you cannot find a <code>fallback</code> or <code>get_default_recs()</code> path, the failure will be total, not degraded.</p>
    """ ,
    "ordering": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Queues and webhooks promise at-least-once, not in-order. A “subscription cancelled” event that is retried can arrive after a “renewed” event and wrongly re-activate a user. The fix is not to force global order — that does not scale — but to make the consumer monotonic: store <code>last_ts</code> per entity and only apply an event if <code>incoming.ts &gt; last_ts</code>. Stale deliveries become no-ops. Sequence numbers work the same way.</p>
    """ ,
    "consistency": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Consistency is the question “which replica did you ask?” The primary has the new row, the read replica is 200ms behind, the cache still holds the old JSON. A user revokes a session, the primary marks it revoked, but the cache still returns “valid” for the next 5 seconds and the revoked token is accepted. The machinery is write-through: in the same transaction that marks revoked, delete the cache key, or version-check on read and treat a cache hit with stale version as a miss.</p>
    """ ,
    "resource-exhaustion": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Every resource has a ceiling: file descriptors, DB connections, memory, queue depth. An unbounded <code>await file.read()</code> loads a 500 MB upload into RAM, the process OOMs, the orchestrator restarts it, the client retries the same upload, and the loop repeats. The fix is to bound: <code>pool(max_size=20)</code>, <code>TokenBucket(capacity=100)</code>, <code>read(64*1024)</code> chunked, and backpressure — when full, return 429, do not queue forever.</p>
    """ ,
    "recovery": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Recovery is the second half of every failure. An at-least-once queue that crashes before ack will redeliver. Without an idempotent consumer, the certificate is sent twice. Without a dead-letter queue, a poison message that always throws JSON parse error will be retried forever, stalling the partition. The machinery is two paths: the happy path acks after durable processing and deduplicates via <code>msg_id UNIQUE</code>, the sad path moves the poison to a DLQ after N attempts and a reconciler sweeps <code>pending</code> rows by asking the provider.</p>
    """ ,
    "observability": """
    <h2 id="how-it-works">How It Works Underneath</h2>
    <p>Observability is not “more logs.” It is “can you answer what happened to operation X?” A <code>print("transfer failed")</code> cannot be joined to a request, a user, or a provider call. Structured logging carries the correlation: <code>trace_id</code> generated at the edge, propagated in <code>X-Request-ID</code> through every service, emitted as JSON <code>{"trace_id": "req_abc", "payment_id": "pay_123", "duration_ms": 42}</code>. Now a single query — <code>trace_id=req_abc</code> — reconstructs the whole timeline across API, worker, and DB.</p>
    """ ,
}

TOOLS = [
    {
        "name": "get_principles",
        "badge": "DISCOVERY",
        "desc": "Returns all 11 failure dimensions, invariants, questions, applicable systems, and mitigation patterns. Supports keyword filtering.",
        "params": [("filter", "string", "Optional search string (e.g. 'timeout', 'payment')", "No")],
        "input_example": '{"filter": "idempotency"}',
        "output_example": '{"principles": [{"id": "idempotency", "name": "Idempotency", "severity": "CRITICAL"}]}'
    },
    {
        "name": "review_architecture",
        "badge": "ANALYSIS",
        "desc": "Analyzes full system descriptions, components, flows, and dependencies. Detects network boundaries, multi-write flows, and surfaces severity-ranked vulnerabilities.",
        "params": [
            ("system", "string", "Description of the system architecture", "Yes"),
            ("components", "list", "List of component names or objects with dependencies", "No"),
            ("flows", "list", "List of critical request paths", "No")
        ],
        "input_example": '{"system": "Checkout API with FastAPI, PostgreSQL, and Stripe"}',
        "output_example": "FAILURE REVIEW — [CRITICAL] External side-effect without idempotency key"
    },
    {
        "name": "analyze_component",
        "badge": "ANALYSIS",
        "desc": "Deep dives into a single architectural component (database, queue, payment, cache, auth, storage, worker).",
        "params": [
            ("component_type", "string", "payment | database | queue | cache | auth | worker | storage", "Yes"),
            ("description", "string", "What this specific component does", "Yes")
        ],
        "input_example": '{"component_type": "payment", "description": "Debits credit cards via Stripe"}',
        "output_example": "COMPONENT REVIEW — [CRITICAL] External charge before DB transaction"
    },
    {
        "name": "review_code",
        "badge": "STATIC CHECK",
        "desc": "Deterministic static AST & regex analyzer for source code. Surfaces failure risks, code evidence excerpts, confidence scores (0.0 - 1.0), and required controls.",
        "params": [
            ("code", "string", "Source code snippet to review", "Yes"),
            ("language", "string", "python | typescript | go", "No")
        ],
        "input_example": '{"code": "await stripe.charge(); await db.execute()", "language": "python"}',
        "output_example": "STATIC FAILURE CHECK — [CRITICAL] External side-effect without idempotency key (Confidence: 0.91)"
    },
    {
        "name": "review_plan",
        "badge": "PLANNING",
        "desc": "Inspects ordered implementation steps BEFORE any code is written. Catches ordering bugs like charging before writing pending state.",
        "params": [
            ("feature", "string", "Feature or user story description", "Yes"),
            ("plan", "list", "Ordered list of step descriptions", "Yes")
        ],
        "input_example": '{"feature": "Checkout", "plan": ["1. Charge Stripe", "2. Save order to DB"]}',
        "output_example": "PLAN REVIEW — [CRITICAL] Step 1 executes external side effect before local state"
    },
    {
        "name": "check_invariant",
        "badge": "VERIFICATION",
        "desc": "Validates whether stated engineering invariants can be violated by failure scenarios in a given architecture, plan, or codebase.",
        "params": [
            ("invariants", "list", "List of predicate statements that must hold true", "Yes")
        ],
        "input_example": '{"invariants": ["payment.never_double_charged"]}',
        "output_example": "INVARIANT CHECK — [VIOLATABLE] payment.never_double_charged under retry timeout"
    },
    {
        "name": "check_idempotency",
        "badge": "SAFETY CHECK",
        "desc": "Dedicated verification on whether an endpoint or function is safely repeatable.",
        "params": [("code", "string", "Code implementation", "Yes")],
        "input_example": '{"code": "def process_order(): db.insert(order)"}',
        "output_example": "IDEMPOTENCY CHECK — NOT_IDEMPOTENT (Missing unique key)"
    },
    {
        "name": "check_retry_safety",
        "badge": "SAFETY CHECK",
        "desc": "Evaluates whether adding retries to a code block will amplify failure or create duplicate side effects.",
        "params": [("code", "string", "Code implementation", "Yes")],
        "input_example": '{"code": "@retry(times=3)\\nasync def charge(): stripe.charge()"}',
        "output_example": "RETRY SAFETY — UNSAFE_FOR_RETRY (Non-idempotent operation retried)"
    },
    {
        "name": "check_transaction_safety",
        "badge": "SAFETY CHECK",
        "desc": "Analyzes database queries and transactions for partial commits, missing rollbacks, and lost updates.",
        "params": [("code", "string", "Code implementation", "Yes")],
        "input_example": '{"code": "await db.execute(\\"UPDATE accounts...\\"); await db.execute(\\"UPDATE orders...\\")"}',
        "output_example": "TRANSACTION SAFETY — UNPROTECTED_MULTI_WRITE"
    },
    {
        "name": "generate_failure_cases",
        "badge": "GENERATION",
        "desc": "Generates concrete, actionable failure scenarios tailored to your system stack.",
        "params": [("system", "string", "System architecture description", "Yes")],
        "input_example": '{"system": "Order fulfillment with RabbitMQ and Postgres"}',
        "output_example": "FAILURE CASES — [HIGH] Worker crash between message processing and queue ACK"
    },
    {
        "name": "generate_failure_tests",
        "badge": "GENERATION",
        "desc": "Generates concrete pytest / jest test definitions covering chaos and failure modes.",
        "params": [("system", "string", "System description", "Yes")],
        "input_example": '{"system": "FastAPI Stripe Checkout"}',
        "output_example": "FAILURE TESTS — test_retry_after_provider_timeout, test_db_crash_after_charge"
    },
    {
        "name": "list_failures",
        "badge": "DISCOVERY",
        "desc": "Lists the full static rule dictionary and failure documents from the internal knowledge base.",
        "params": [("filter", "string", "Optional filter string", "No")],
        "input_example": '{"filter": "concurrency"}',
        "output_example": '{"rules": [{"id": "race_condition_read_modify_write", "severity": "HIGH"}]}'
    }
]

PATTERNS = [
    {
        "id": "idempotency-key",
        "name": "Idempotency Key Pattern",
        "badge": "CRITICAL MITIGATION",
        "principles": ["Idempotency", "Timeout", "Retry Safety"],
        "desc": "Client-generated unique token attached to mutating requests. The server checks the key, executes, and saves response for immediate deduplication on retries.",
        "code": """@app.post("/api/v1/payments")
async def create_payment(payload: PaymentRequest, key: str = Header(..., alias="Idempotency-Key"), db: AsyncSession = Depends(get_db)):
    existing = await db.fetch_one("SELECT * FROM idempotency_keys WHERE key = :key", {"key": key})
    if existing and existing.status == "completed": return json.loads(existing.response_body)
    await db.execute("INSERT INTO idempotency_keys (key, status) VALUES (:key, 'pending')", {"key": key})
    charge = await stripe.charge(payload.amount, idempotency_key=key)
    await db.execute("UPDATE idempotency_keys SET status = 'completed', response_body = :resp WHERE key = :key", {"key": key, "resp": json.dumps(charge)})
    return charge"""
    },
    {
        "id": "transactional-outbox",
        "name": "Transactional Outbox Pattern",
        "badge": "ATOMICITY & EVENTS",
        "principles": ["Atomicity", "Consistency", "Recovery"],
        "desc": "Solves Dual-Write bugs by persisting outgoing events into an 'outbox' table in the exact same DB transaction as domain mutations. A background relay dispatches them.",
        "code": """async def complete_order(order_id: str, db: AsyncSession):
    async with db.begin():
        await db.execute("UPDATE orders SET status = 'paid' WHERE id = :id", {"id": order_id})
        await db.execute("INSERT INTO outbox_events (id, payload, status) VALUES (:id, :payload, 'pending')", {"id": str(uuid4()), "payload": json.dumps({"order_id": order_id})})"""
    },
    {
        "id": "circuit-breaker",
        "name": "Circuit Breaker Pattern",
        "badge": "AVAILABILITY & RESILIENCE",
        "principles": ["Availability", "Resource Exhaustion"],
        "desc": "Wraps fragile dependencies. Trips to OPEN state on repeated failures to fail fast without locking up worker threads.",
        "code": """class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"
        self.failures = 0
    def allow_request(self):
        if self.state == "OPEN": return False
        return True"""
    },
    {
        "id": "optimistic-locking",
        "name": "Optimistic Locking Pattern",
        "badge": "CONCURRENCY CONTROL",
        "principles": ["Concurrency", "Consistency"],
        "desc": "Records include numeric version columns. Updates include WHERE id = :id AND version = :expected. If another worker updated first, 0 rows are updated.",
        "code": """async def update_inventory(item_id: str, delta: int):
    item = await db.fetch_one("SELECT stock, version FROM inventory WHERE id = %s", item_id)
    res = await db.execute("UPDATE inventory SET stock = stock + %s, version = version + 1 WHERE id = %s AND version = %s", delta, item_id, item['version'])
    if res.rows_affected == 0: raise ConcurrencyConflictException()"""
    }
]

def render_topbar(active_tab="docs", depth=0):
    root_rel = "../" * depth if depth > 0 else ""
    return f"""<header class="fixed top-0 left-0 right-0 z-50 flex items-stretch gap-0 h-[45px] bg-background/95 backdrop-blur-sm">
  <!-- Left brand (40%) — logo + search + theme + mobile toggle -->
  <div class="w-full lg:w-[40%] flex items-center justify-between px-5 sm:px-6 lg:px-7 lg:border-r border-foreground/[0.06] shrink-0">
    <a href="{root_rel}index.html" class="flex items-center gap-2.5 text-foreground hover:opacity-85 transition-opacity">
      {FAILURES_LOGO}
      <span class="font-semibold text-[14px] tracking-tight" style="font-family: var(--font-geist-sans); letter-spacing: -0.02em;">Failures</span>
    </a>
    <div class="flex items-center gap-0.5">
      <!-- Hamburger — mobile ONLY, hidden on lg+ via CSS -->
      <button type="button" class="ba-mobile-nav-btn lg:hidden flex items-center justify-center size-8 text-foreground/60 hover:text-foreground transition-colors" data-mobile-toggle aria-label="Open menu">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>
      </button>
    </div>
  </div>

  <!-- Right navigation tabs (60%) — desktop only, shown via CSS ba-desktop-tabs -->
  <div class="ba-desktop-tabs hidden lg:flex flex-1 items-stretch min-w-0">
    <nav class="flex-1 flex items-stretch">
      <a class="relative flex-1 flex items-center justify-center gap-1.5 px-2 xl:px-4 h-full border-r border-foreground/[0.06] transition-colors duration-150 font-mono text-xs uppercase tracking-wider whitespace-nowrap {'border-b-2 border-b-foreground text-foreground font-semibold bg-foreground/[0.02]' if active_tab == 'home' else 'text-foreground/65 dark:text-foreground/50 hover:bg-foreground/[0.03] hover:text-foreground/80'}" href="{root_rel}index.html">readme</a>
      <a class="relative flex-1 flex items-center justify-center gap-1.5 px-2 xl:px-4 h-full border-r border-foreground/[0.06] transition-colors duration-150 font-mono text-xs uppercase tracking-wider whitespace-nowrap {'border-b-2 border-b-foreground text-foreground font-semibold bg-foreground/[0.02]' if active_tab == 'docs' else 'text-foreground/65 dark:text-foreground/50 hover:bg-foreground/[0.03] hover:text-foreground/80'}" href="{root_rel}docs/index.html">docs</a>
      <a class="relative flex-1 flex items-center justify-center gap-1.5 px-2 xl:px-4 h-full border-r border-foreground/[0.06] transition-colors duration-150 font-mono text-xs uppercase tracking-wider whitespace-nowrap {'border-b-2 border-b-foreground text-foreground font-semibold bg-foreground/[0.02]' if active_tab == 'tools' else 'text-foreground/65 dark:text-foreground/50 hover:bg-foreground/[0.03] hover:text-foreground/80'}" href="{root_rel}docs/tools.html">tools</a>
      <a class="relative flex-1 flex items-center justify-center gap-1.5 px-2 xl:px-4 h-full border-r border-foreground/[0.06] transition-colors duration-150 font-mono text-xs uppercase tracking-wider whitespace-nowrap {'border-b-2 border-b-foreground text-foreground font-semibold bg-foreground/[0.02]' if active_tab == 'patterns' else 'text-foreground/65 dark:text-foreground/50 hover:bg-foreground/[0.03] hover:text-foreground/80'}" href="{root_rel}docs/patterns.html">patterns</a>
      <a class="relative flex-1 flex items-center justify-center gap-1.5 px-2 xl:px-4 h-full border-r border-foreground/[0.06] transition-colors duration-150 font-mono text-xs uppercase tracking-wider whitespace-nowrap {'border-b-2 border-b-foreground text-foreground font-semibold bg-foreground/[0.02]' if active_tab == 'examples' else 'text-foreground/65 dark:text-foreground/50 hover:bg-foreground/[0.03] hover:text-foreground/80'}" href="{root_rel}docs/examples.html">benchmark</a>
    </nav>
    <!-- Rightmost GitHub CTA -->
    <a href="https://github.com/mayowa-kalejaiye/Failures" target="_blank" class="flex items-center gap-2 px-5 bg-foreground text-background hover:opacity-90 transition-opacity shrink-0">
      <span class="font-mono text-xs uppercase tracking-wider font-semibold">GitHub</span>
      <svg class="h-2.5 w-2.5 opacity-60" viewBox="0 0 10 10" fill="none"><path d="M1 9L9 1M9 1H3M9 1V7" stroke="currentColor" stroke-width="1.3"></path></svg>
    </a>
  </div>
</header>

<!-- Mobile Navigation Slideout — CSS controls display via #mobile-nav-drawer / #mobile-nav-drawer.open -->
<div id="mobile-nav-drawer" class="fixed inset-0 z-[100] bg-background/95 backdrop-blur-md flex-col p-6 pointer-events-auto">
  <div class="flex items-center justify-between pb-4 border-b border-foreground/[0.08]">
    <div class="flex items-center gap-2 font-mono font-bold text-sm">
      {FAILURES_LOGO}
      <span>Failures</span>
    </div>
    <button type="button" data-mobile-close class="flex items-center justify-center size-8 text-foreground/60 hover:text-foreground" aria-label="Close menu">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  </div>
  <nav class="flex flex-col gap-4 py-6 font-mono text-sm uppercase tracking-wider">
    <a href="{root_rel}index.html" class="py-2 border-b border-foreground/[0.04]">readme</a>
    <a href="{root_rel}docs/index.html" class="py-2 border-b border-foreground/[0.04]">docs</a>
    <a href="{root_rel}docs/tools.html" class="py-2 border-b border-foreground/[0.04]">tools</a>
    <a href="{root_rel}docs/patterns.html" class="py-2 border-b border-foreground/[0.04]">patterns</a>
    <a href="{root_rel}docs/examples.html" class="py-2 border-b border-foreground/[0.04]">benchmark</a>
  </nav>
  <a href="https://github.com/mayowa-kalejaiye/Failures" target="_blank" class="mt-auto flex items-center justify-center gap-2 py-3 bg-foreground text-background font-mono text-xs uppercase tracking-wider font-semibold">
    <span>GitHub</span>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
  </a>
</div>"""

def render_search_dialog():
    return f"""<div id="search-overlay" class="ba-search-overlay" role="dialog" aria-modal="true">
  <div class="ba-search-dialog">
    <div class="ba-search-input-wrap">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      <input type="text" id="search-input" class="ba-search-input" placeholder="Search principles, tools, patterns..." autocomplete="off">
    </div>
    <div id="search-results" class="ba-search-results"></div>
    <div class="ba-search-footer">
      <span><kbd>Esc</kbd> to close</span>
      <span><kbd>↵</kbd> to navigate</span>
    </div>
  </div>
</div>"""

def render_features_bento():
    return """<div class="flex items-center gap-4 my-6">
  <span class="text-lg font-medium text-foreground/90 dark:text-foreground/80 tracking-tight shrink-0">Features</span>
  <div class="flex-1 border-t border-foreground/10"></div>
</div>

<div class="relative grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 mb-6 border border-foreground/[0.08] bg-foreground/[0.08] gap-px overflow-hidden">
  <!-- Card 01: Works with your Agent Stack -->
  <a class="contents" href="docs/index.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-2">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">01</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">Works with your Agent Stack.</div>
      </div>
      <div class="text-[12px] text-neutral-500 dark:text-neutral-400 leading-snug transition-colors duration-200 group-hover/card:text-neutral-300 mb-3">Claude Code, Cursor, Cline, Windsurf, Devin, and all MCP clients.</div>
      <div class="flex items-center gap-3 mt-auto">
        <!-- Claude Code — Anthropic starburst -->
        <div class="text-neutral-700 dark:text-neutral-300 opacity-80 transition-all duration-300 group-hover/card:opacity-100 group-hover/card:animate-[icon-bounce_0.4s_ease-out_0s]" title="Claude Code">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>
        </div>
        <!-- Cursor — pointer cursor shape -->
        <div class="text-neutral-700 dark:text-neutral-300 opacity-80 transition-all duration-300 group-hover/card:opacity-100 group-hover/card:animate-[icon-bounce_0.4s_ease-out_0.06s]" title="Cursor">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M3.97 2.03a.75.75 0 0 0-1.03.72v18.5a.75.75 0 0 0 1.28.53l4.56-4.56h8.44a.75.75 0 0 0 .53-1.28l-13-13a.75.75 0 0 0-.78-.16z"/></svg>
        </div>
        <!-- Cline — terminal prompt -->
        <div class="text-neutral-700 dark:text-neutral-300 opacity-80 transition-all duration-300 group-hover/card:opacity-100 group-hover/card:animate-[icon-bounce_0.4s_ease-out_0.12s]" title="Cline">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
        </div>
        <!-- Windsurf — wave arcs -->
        <div class="text-neutral-700 dark:text-neutral-300 opacity-80 transition-all duration-300 group-hover/card:opacity-100 group-hover/card:animate-[icon-bounce_0.4s_ease-out_0.18s]" title="Windsurf">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 19c2-4 5-6 8-6s6 2 8 6"/><path d="M5 13c1.5-3.5 4-5.5 7-5.5s5.5 2 7 5.5"/><path d="M9 7.5c1-3 2.5-4.5 3-4.5s2 1.5 3 4.5"/></svg>
        </div>
        <!-- Devin — robot agent face -->
        <div class="text-neutral-700 dark:text-neutral-300 opacity-80 transition-all duration-300 group-hover/card:opacity-100 group-hover/card:animate-[icon-bounce_0.4s_ease-out_0.24s]" title="Devin">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="10" r="1.5" fill="currentColor"/><circle cx="15" cy="10" r="1.5" fill="currentColor"/><path d="M9 15h6"/></svg>
        </div>
        <div class="flex items-center justify-center size-[20px] border border-dashed border-foreground/[0.1] text-foreground/35 dark:text-foreground/20">
          <span class="text-[7px] font-mono leading-none">+8</span>
        </div>
      </div>
    </div>
  </a>

  <!-- Card 02: Deterministic AST Analysis -->
  <a class="contents" href="docs/tools.html#tool-review-code">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">02</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">Deterministic AST analysis.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">AST evidence extraction and honest confidence scoring (0.0 to 1.0).</div>
      <div class="mt-3 flex items-center gap-1.5 min-w-0">
        <div class="flex items-center h-5 px-2 border border-foreground/[0.08] bg-foreground/[0.02] flex-1 min-w-0 overflow-hidden">
          <span class="text-[9px] font-mono text-purple-400 mr-1.5 shrink-0">AST</span>
          <span class="text-[9px] font-mono text-foreground/50 dark:text-foreground/35 truncate min-w-0">ast.Call(stripe.charge)</span>
        </div>
        <div class="flex items-center h-5 px-2 border border-foreground/[0.08] bg-foreground/[0.02] flex-1 min-w-0 overflow-hidden">
          <span class="text-[9px] font-mono text-emerald-400 mr-1.5 shrink-0">CONF</span>
          <span class="text-[9px] font-mono text-foreground/50 dark:text-foreground/35 truncate min-w-0">0.91 [CRITICAL]</span>
        </div>
      </div>
    </div>
  </a>

  <!-- Card 03: 13 Core MCP Tools -->
  <a class="contents" href="docs/tools.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">03</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">13 Core MCP Tools.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">review_code, review_plan, check_invariant, and test generation.</div>
      <div class="mt-3 relative overflow-hidden">
        <div class="flex items-center gap-1.5">
          <div class="flex items-center h-6 px-2 border border-foreground/10 bg-background text-[8px] font-mono text-foreground/70">review_code()</div>
          <div class="flex items-center h-6 px-2 border border-foreground/10 bg-background text-[8px] font-mono text-foreground/70">check_invariant()</div>
          <div class="flex items-center justify-center size-6 border border-dashed border-foreground/[0.1] text-foreground/35 text-[8px] font-mono">+10</div>
        </div>
      </div>
    </div>
  </a>

  <!-- Card 04: Invariant Contracts -->
  <a class="contents" href="docs/principles/atomicity.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">04</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">11 Failure Dimensions.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">Formal invariant contracts across distributed races, crashes, and timeouts.</div>
      <div class="mt-3 flex items-center gap-2.5">
        <div class="flex -space-x-1.5">
          <div class="size-5 rounded-full border border-foreground/10 bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 flex items-center justify-center text-[8px] font-mono z-[3]">A</div>
          <div class="size-5 rounded-full border border-foreground/10 bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 flex items-center justify-center text-[8px] font-mono z-[2]">I</div>
          <div class="size-5 rounded-full border border-foreground/10 bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 flex items-center justify-center text-[8px] font-mono z-[1]">T</div>
          <div class="size-5 rounded-full border border-dashed border-foreground/20 bg-background flex items-center justify-center text-[8px] font-mono">+8</div>
        </div>
        <div class="flex flex-wrap items-center gap-1">
          <span class="text-[8px] font-mono text-red-400 px-1.5 py-0.5 border border-red-500/20 bg-red-500/5 shrink-0 whitespace-nowrap">CRITICAL</span>
          <span class="text-[8px] font-mono text-orange-400 px-1.5 py-0.5 border border-orange-500/20 bg-orange-500/5 shrink-0 whitespace-nowrap">HIGH</span>
          <span class="text-[8px] font-mono text-yellow-400 px-1.5 py-0.5 border border-yellow-500/20 bg-yellow-500/5 shrink-0 whitespace-nowrap">MEDIUM</span>
        </div>
      </div>
    </div>
  </a>

  <!-- Card 05: Enterprise Resilience -->
  <a class="contents" href="docs/patterns.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">05</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">Enterprise Resilience.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">Transactional outboxes, circuit breakers, optimistic locks, and DLQs.</div>
      <div class="mt-3 flex items-center gap-2.5">
        <div class="flex items-center gap-2">
          <div class="size-6 flex items-center justify-center border border-foreground/10 bg-background text-neutral-200">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/></svg>
          </div>
          <div class="size-6 flex items-center justify-center border border-foreground/10 bg-background text-neutral-200">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </div>
          <div class="size-6 flex items-center justify-center border border-foreground/10 bg-background text-neutral-200">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305"/></svg>
          </div>
          <div class="size-6 flex items-center justify-center border border-dashed border-foreground/20 text-[8px] font-mono">+</div>
        </div>
      </div>
    </div>
  </a>

  <!-- Card 06: 50+ Cataloged Failure Modes -->
  <a class="contents" href="docs/patterns.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background-0 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">06</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">50+ Cataloged Failure Modes.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">Partial commits, phantom retries, lost updates, OOMs, and split-brains.</div>
      <div class="mt-3 relative overflow-hidden">
        <div class="flex items-center gap-1 overflow-hidden">
          <span class="text-[8px] font-mono px-1.5 py-0.5 border border-foreground/10 bg-foreground/[0.02] shrink-0">partial-commit</span>
          <span class="text-[8px] font-mono px-1.5 py-0.5 border border-foreground/10 bg-foreground/[0.02] shrink-0">lost-update</span>
          <span class="text-[8px] font-mono px-1.5 py-0.5 border border-foreground/10 bg-foreground/[0.02] shrink-0">retry-storm</span>
          <span class="text-[8px] font-mono px-1.5 py-0.5 border border-foreground/10 bg-foreground/[0.02] shrink-0">poison-pill</span>
        </div>
        <div class="absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-background to-transparent pointer-events-none"></div>
      </div>
    </div>
  </a>

  <!-- Card 07: Protocol for AI Coding Agents -->
  <a class="contents" href="docs/index.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">07</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">Protocol for AI Agents.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">Model Context Protocol interception for autonomous coding agents.</div>
      <div class="mt-3 flex items-center h-5 px-2.5 border border-foreground/[0.06] bg-foreground/[0.015] font-mono text-[8px] gap-1 overflow-hidden min-w-0">
        <span class="text-foreground/30 shrink-0">$</span>
        <span class="text-foreground/70 truncate min-w-0">failures.audit(ast)</span>
        <span class="text-foreground/30 shrink-0">→</span>
        <span class="text-emerald-400 shrink-0"><span class="inline-flex items-center gap-1 whitespace-nowrap">0 findings <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></span></span>
        <span class="inline-block w-px h-2.5 bg-foreground/30 animate-[blink_1s_steps(2)_infinite] shrink-0"></span>
      </div>
    </div>
  </a>

  <!-- Card 08: Automated Chaos Testing -->
  <a class="contents" href="docs/examples.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">08</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">Automated Chaos Testing.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">Pytest and Jest suite generation for timeouts and crash recovery.</div>
      <div class="mt-3 flex flex-wrap items-center gap-1.5 font-mono text-[8px]">
        <div class="flex items-center gap-1 px-1.5 py-0.5 border border-red-500/20 bg-red-500/5 shrink-0 whitespace-nowrap">
          <span class="size-1 rounded-full bg-red-400 shrink-0"></span>
          <span class="text-red-400">CRITICAL (0.91)</span>
        </div>
        <div class="flex items-center gap-1 px-1.5 py-0.5 border border-amber-500/20 bg-amber-500/5 shrink-0 whitespace-nowrap">
          <span class="size-1 rounded-full bg-amber-400 shrink-0"></span>
          <span class="text-amber-400">HIGH (0.84)</span>
        </div>
        <div class="flex items-center gap-1 px-1.5 py-0.5 border border-emerald-500/20 bg-emerald-500/5 shrink-0 whitespace-nowrap">
          <span class="size-1 rounded-full bg-emerald-400 shrink-0"></span>
          <span class="text-emerald-400">VERIFIED (1.0)</span>
        </div>
      </div>
    </div>
  </a>

  <!-- Card 09: Sentinel Live Telemetry Ticker -->
  <a class="contents" href="docs/examples.html">
    <div class="group/card relative p-4 lg:p-5 min-h-[100px] transition-all duration-200 hover:bg-foreground/[0.02] hover:shadow-[inset_0_1px_0_0_rgba(128,128,128,0.1)] hover:z-10 bg-background">
      <span class="absolute top-3 right-3 lg:top-4 lg:right-4 opacity-0 -translate-y-0.5 group-hover/card:opacity-100 group-hover/card:translate-y-0 transition-all duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-foreground/40 dark:text-foreground/50"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
      </span>
      <div class="mb-1">
        <div class="text-[11px] font-mono text-foreground/45 dark:text-foreground/30 tracking-wider transition-colors duration-200 group-hover/card:text-foreground/60">09</div>
        <div class="text-[13px] font-medium text-foreground/80 dark:text-neutral-100 transition-colors duration-200">Sentinel Live Telemetry.</div>
      </div>
      <div class="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed transition-colors duration-200 group-hover/card:text-neutral-300">Continuous telemetry and verification of invariants under failure.</div>
      <div class="mt-3 relative overflow-hidden h-5">
        <div class="flex animate-[marquee_20s_linear_infinite] gap-4">
          <div class="flex gap-4 shrink-0">
            <div class="flex items-center gap-1.5 shrink-0 h-5 whitespace-nowrap">
              <span class="text-[8px] font-mono text-foreground/30">10:50 AM</span>
              <span class="text-[8px] font-mono text-emerald-400">Sentinel:</span>
              <span class="text-[8px] font-mono text-foreground/50">verified transactional outbox</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0 h-5 whitespace-nowrap">
              <span class="text-[8px] font-mono text-foreground/30">10:48 AM</span>
              <span class="text-[8px] font-mono text-purple-400">Invariant:</span>
              <span class="text-[8px] font-mono text-foreground/50">checked payment.not_double_charged</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0 h-5 whitespace-nowrap">
              <span class="text-[8px] font-mono text-foreground/30">10:45 AM</span>
              <span class="text-[8px] font-mono text-amber-400">Chaos:</span>
              <span class="text-[8px] font-mono text-foreground/50">simulated network partition</span>
            </div>
          </div>
          <div class="flex gap-4 shrink-0">
            <div class="flex items-center gap-1.5 shrink-0 h-5 whitespace-nowrap">
              <span class="text-[8px] font-mono text-foreground/30">10:50 AM</span>
              <span class="text-[8px] font-mono text-emerald-400">Sentinel:</span>
              <span class="text-[8px] font-mono text-foreground/50">verified transactional outbox</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0 h-5 whitespace-nowrap">
              <span class="text-[8px] font-mono text-foreground/30">10:48 AM</span>
              <span class="text-[8px] font-mono text-purple-400">Invariant:</span>
              <span class="text-[8px] font-mono text-foreground/50">checked payment.not_double_charged</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0 h-5 whitespace-nowrap">
              <span class="text-[8px] font-mono text-foreground/30">10:45 AM</span>
              <span class="text-[8px] font-mono text-amber-400">Chaos:</span>
              <span class="text-[8px] font-mono text-foreground/50">simulated network partition</span>
            </div>
          </div>
        </div>
        <div class="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-background to-transparent pointer-events-none"></div>
      </div>
    </div>
  </a>

  <!-- 4 Intersection Crosshair Markers -->
  <span class="hidden md:block absolute top-1/3 left-1/3 -translate-x-1/2 -translate-y-1/2 font-mono text-[10px] text-foreground/35 select-none z-10">+</span>
  <span class="hidden md:block absolute top-1/3 left-2/3 -translate-x-1/2 -translate-y-1/2 font-mono text-[10px] text-foreground/35 select-none z-10">+</span>
  <span class="hidden md:block absolute top-2/3 left-1/3 -translate-x-1/2 -translate-y-1/2 font-mono text-[10px] text-foreground/35 select-none z-10">+</span>
  <span class="hidden md:block absolute top-2/3 left-2/3 -translate-x-1/2 -translate-y-1/2 font-mono text-[10px] text-foreground/35 select-none z-10">+</span>
</div>"""

def build_landing_page():
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Failures — Engineering failure invariants for AI-built software</title>
  <meta name="description" content="Engineering constraints for AI-built software. Make your coding agent reason about failure modes.">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
    .ba-landing .lg\:w-\[60\%] {{
      scroll-margin-top: 80px;
    }}
    @media (min-width: 1024px) {{
      .ba-landing .lg\:w-\[60\%] {{
        padding-top: 40px;
      }}
    }}
    .ba-readme-header {{
      padding-top: 32px;
      scroll-margin-top: 80px;
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }},
          keyframes: {{
            'icon-bounce': {{
              '0%, 100%': {{ transform: 'translateY(0)' }},
              '50%': {{ transform: 'translateY(-3px)' }},
            }},
            marquee: {{
              '0%': {{ transform: 'translateX(0%)' }},
              '100%': {{ transform: 'translateX(-50%)' }},
            }},
            blink: {{
              '0%, 100%': {{ opacity: '1' }},
              '50%': {{ opacity: '0' }},
            }}
          }},
          animation: {{
            'icon-bounce': 'icon-bounce 0.4s ease-out',
            marquee: 'marquee 20s linear infinite',
            blink: 'blink 1s steps(2) infinite',
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body class="ba-landing">
  {render_topbar(active_tab="home", depth=0)}

  <div id="hero" class="relative pt-[45px] lg:pt-0">
    <div class="relative text-foreground" data-v="1">
      <div class="flex flex-col lg:flex-row gap-0">
        <!-- LEFT COLUMN (40% Sticky) -->
        <div class="ba-sticky-left relative w-full lg:w-[40%] lg:h-[calc(100vh-45px)] lg:border-r border-foreground/[0.06] px-5 sm:px-6 lg:px-7 lg:sticky lg:top-[45px] z-10 bg-background lg:overflow-clip">
          <div class="hidden lg:block absolute inset-0 overflow-hidden bg-background pointer-events-none" aria-hidden="true">
            <div class="ba-hero-linefield-overlay"></div>
            <canvas id="hero-linefield" class="w-full h-full invert opacity-60 dark:invert-0 dark:opacity-70"></canvas>
            <svg class="absolute inset-0 w-full h-full" viewBox="0 0 400 260" preserveAspectRatio="none" aria-hidden="true">
              <defs><linearGradient id="fail-grad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="currentColor" stop-opacity="0"/><stop offset="12%" stop-color="currentColor" stop-opacity="0.18"/><stop offset="50%" stop-color="currentColor" stop-opacity="0.18"/><stop offset="88%" stop-color="currentColor" stop-opacity="0"/></linearGradient></defs>
              <g stroke="currentColor" stroke-opacity="0.05" stroke-width="0.6"><line x1="0" y1="52" x2="400" y2="52"/><line x1="0" y1="104" x2="400" y2="104"/><line x1="0" y1="156" x2="400" y2="156"/><line x1="0" y1="208" x2="400" y2="208"/></g>
              <path d="M 0 130 L 80 130 L 110 130 L 140 132 L 175 131 L 210 131 L 260 131 L 320 130 L 400 130" fill="none" stroke="#10b981" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.22" style="stroke-dasharray: 3 5;"/>
              <path d="M 0 130 L 70 130 L 95 118 L 115 146 L 132 86 L 148 154 L 165 121 L 185 131 L 210 131 L 400 131" fill="none" stroke="#f59e0b" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.28"/>
              <path d="M 0 130 L 110 130 L 135 130 L 145 68 L 155 196 L 168 130 L 205 130 L 225 130 L 240 130 L 400 130" fill="none" stroke="#ef4444" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.26"/>
              <rect x="112" y="44" width="96" height="88" rx="6" fill="none" stroke="currentColor" stroke-opacity="0.07" stroke-width="0.8" stroke-dasharray="4 4"/>
              <g font-family="Geist Mono, monospace" font-size="6.2" fill="currentColor" opacity="0.32"><text x="116" y="54">AMBIGUOUS</text><text x="116" y="62" opacity="0.22">timeout → retry?</text></g>
              <g font-family="Geist Mono, monospace" font-size="5.8"><rect x="264" y="118" rx="3" width="58" height="14" fill="#10b981" opacity="0.12" stroke="#10b981" stroke-opacity="0.18"/><text x="293" y="127.5" text-anchor="middle" fill="#059669" opacity="0.9">invariant ✓</text></g>
            </svg>
          </div>
          <div class="flex justify-center h-full absolute items-center left-[26%] lg:left-[30%] w-full max-w-[400px] lg:max-w-[360px] pointer-events-auto select-none animate-logo-reveal z-[2] opacity-100">
                      <div class="group relative max-w-[360px] w-full flex justify-center opacity-100 -mt-[38%] lg:-mt-[58%]">
            <div class="relative size-[160px] lg:size-[200px] rounded-full bg-[#ef4444]/[0.08] border border-[#ef4444]/[0.12] flex items-center justify-center backdrop-blur-[0.5px] transition-transform duration-300 ease-out group-hover:scale-[1.03] group-hover:rotate-1">
              <div class="size-[104px] lg:size-[128px] rounded-full bg-[#ef4444] flex items-center justify-center shadow-[0_8px_24px_rgba(239,68,68,0.22)]">
                <svg width="52" height="52" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 10 L22 22 M22 10 L10 22" stroke="white" stroke-width="3.2" stroke-linecap="round"/>
                </svg>
              </div>
              <span class="absolute -bottom-1 -right-1 size-6 rounded-full bg-foreground text-background flex items-center justify-center text-[10px] font-mono font-bold">×</span>
            </div>
          </div>
          </div>
          <div class="relative z-[3] w-full py-12 lg:py-0 flex flex-col justify-center h-full pointer-events-none">
            <div>
              <a class="relative inline-flex items-center gap-1.5 px-2.5 py-1 pointer-events-auto group/badge rounded-full bg-neutral-200/80 dark:bg-neutral-800/80 hover:bg-neutral-200/70 dark:hover:bg-neutral-700/50 transition-colors" href="docs/index.html">
                <svg width="14" height="14" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="shrink-0">
                  <rect width="32" height="32" rx="7" fill="currentColor" fill-opacity="0.12"/>
                  <path d="M9 8h14" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                  <path d="M9 16h9" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                  <path d="M9 8v16" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                  <circle cx="23" cy="23" r="6.5" fill="#ef4444"/>
                  <path d="M20.5 20.5l5 5M25.5 20.5l-5 5" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
                <span class="text-xs sm:text-sm text-neutral-600 dark:text-neutral-100 font-light">Announcement <span class="font-medium">| Failures MCP v0.3.1 is Live</span></span>
                <svg xmlns="http://www.w3.org/2000/svg" width="0.85em" height="0.85em" viewBox="0 0 24 24" class="text-neutral-500 dark:text-neutral-400 transition-transform group-hover/badge:translate-x-0.5" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14m-6-6l6 6l-6 6"></path></svg>
              </a>
              <h1 class="pt-3 sm:pt-4 text-2xl md:text-3xl xl:text-4xl text-neutral-800 dark:text-neutral-200 tracking-tight leading-tight text-balance">
                Engineering failure invariants for AI-built software
              </h1>
              <div class="flex flex-wrap items-center gap-2 sm:gap-3 pt-4 sm:pt-5 pointer-events-auto">
                <a class="inline-flex items-center gap-1.5 px-4 sm:px-5 py-2 bg-neutral-900 text-neutral-100 dark:bg-neutral-100 dark:text-neutral-900 text-xs sm:text-sm font-medium hover:opacity-90 transition-colors" href="docs/index.html">Get Started</a>
                <a class="relative inline-flex items-center gap-1.5 px-4 sm:px-5 py-2 text-neutral-600 dark:text-neutral-300 text-xs sm:text-sm font-medium transition-colors group" href="docs/tools.html">
                  <span class="absolute inset-0 opacity-[0.04] group-hover:opacity-[0.08] transition-opacity" style="background-image:repeating-linear-gradient(-45deg, transparent, transparent 4px, currentColor 4px, currentColor 5px)"></span>
                  <span class="absolute top-0 -left-[6px] -right-[6px] h-px bg-foreground/20 group-hover:bg-foreground/30 transition-colors"></span>
                  <span class="absolute bottom-0 -left-[6px] -right-[6px] h-px bg-foreground/20 group-hover:bg-foreground/30 transition-colors"></span>
                  <span class="absolute left-0 -top-[6px] -bottom-[6px] w-px bg-foreground/20 group-hover:bg-foreground/30 transition-colors"></span>
                  <span class="absolute right-0 -top-[6px] -bottom-[6px] w-px bg-foreground/20 group-hover:bg-foreground/30 transition-colors"></span>
                  <span class="absolute -bottom-[6px] -right-[6px] font-mono text-[8px] text-foreground/40 dark:text-foreground/50 leading-none select-none translate-x-1/2 translate-y-1/2">+</span>
                  <span class="relative">Install MCP</span>
                </a>
              </div>
            </div>
          </div>
          <!-- Bottom Meta Bar: ALWAYS pinned on desktop and visible on mobile -->
          <div class="ba-bottom-meta block absolute left-5 right-5 lg:left-7 lg:right-7 bottom-4 z-20">
            <div class="flex items-center justify-between gap-3 text-[11px] font-mono text-foreground/50 select-none">
              <div class="flex items-center gap-3">
                <a class="hover:text-foreground/80 transition-colors" href="docs/index.html">Docs</a>
                <span class="text-foreground/15">/</span>
                <a class="hover:text-foreground/80 transition-colors" href="docs/tools.html">Tools</a>
                <span class="text-foreground/15">/</span>
                <a class="hover:text-foreground/80 transition-colors" href="docs/examples.html">Benchmark</a>
              </div>
              <div class="flex items-center gap-3">
                <a aria-label="GitHub" class="text-foreground/50 hover:text-foreground/80 transition-colors" href="https://github.com/mayowa-kalejaiye/Failures" target="_blank">{COMPANY_LOGOS['github']}</a>
                <a aria-label="X" class="text-foreground/50 hover:text-foreground/80 transition-colors" href="https://x.com/MayowaSWE" target="_blank"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
                <button type="button" data-theme-toggle class="flex items-center justify-center size-6 text-foreground/50 hover:text-foreground/80 transition-colors" title="Toggle theme" aria-label="Toggle theme">
        <span data-theme-icon="light"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg></span>
        <span data-theme-icon="dark" class="hidden"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg></span>
      </button>
              </div>
            </div>
          </div>
        </div>



        <!-- RIGHT COLUMN (60% Scrollable) -->
        <div class="relative w-full lg:w-[60%] px-5 sm:px-6 lg:px-8 py-8 lg:py-12">
          <div class="ba-readme-header">
            <span>README</span>
          </div>

          <p class="ba-readme-lead">
            Engineering invariants that live <strong>inside your coding agent</strong>. 11 failure dimensions, 50+ cataloged modes, AST-verified with zero tokens — deterministic checks, not prompts.
          </p>

          <!-- Multi-tab Command Box (CLI / Prompt / MCP / Skills) -->
          <div class="ba-cmd-box">
            <div class="ba-cmd-tabs">
              <button class="ba-cmd-tab active" data-tab="cli">CLI</button>
              <button class="ba-cmd-tab" data-tab="mcp">MCP Config</button>
              <button class="ba-cmd-tab" data-tab="prompt">Prompt</button>
              <button class="ba-cmd-tab" data-tab="skills">Skills</button>
            </div>
            <div class="ba-cmd-content">
              <div id="tab-cli" class="ba-cmd-snippet active">
                <span style="color:#a855f7; font-weight:600;">pip</span>
                <span>install failures-mcp &amp;&amp; failures-mcp</span>
              </div>
              <div id="tab-mcp" class="ba-cmd-snippet">
                <span style="color:#f97316; font-weight:600;">mcp</span>
                <span>{{"failures": {{"command": "failures-mcp", "args": []}}}}</span>
              </div>
              <div id="tab-prompt" class="ba-cmd-snippet">
                <span style="color:#eab308; font-weight:600;">ask</span>
                <span>"Audit this checkout flow against all 11 failure dimensions."</span>
              </div>
              <div id="tab-skills" class="ba-cmd-snippet">
                <span style="color:#6366f1; font-weight:600;">skill</span>
                <span>failures.review_code(language="python")</span>
              </div>
              <button class="ba-btn-icon copy-btn" data-copy="tab-cli" aria-label="Copy code">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
            </div>
          </div>

          <!-- "Trusted By" Marquee with Agent Ecosystem Logos -->
          <div class="ba-trusted-label">Works with your agent stack</div>
          <div class="ba-marquee-wrap">
            <div class="ba-marquee">
              <div class="ba-marquee-item">{COMPANY_LOGOS['claude']}<span>Claude Code</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['cursor']}<span>Cursor</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['cline']}<span>Cline</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['windsurf']}<span>Windsurf</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['openai']}<span>OpenAI Operator</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['stripe']}<span>Stripe SDK</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['postgres']}<span>PostgreSQL</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['supabase']}<span>Supabase</span></div>
              <!-- Repeat for infinite marquee loop -->
              <div class="ba-marquee-item">{COMPANY_LOGOS['claude']}<span>Claude Code</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['cursor']}<span>Cursor</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['cline']}<span>Cline</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['windsurf']}<span>Windsurf</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['openai']}<span>OpenAI Operator</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['stripe']}<span>Stripe SDK</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['postgres']}<span>PostgreSQL</span></div>
              <div class="ba-marquee-item">{COMPANY_LOGOS['supabase']}<span>Supabase</span></div>
            </div>
          </div>

          <!-- EXACT 3x3 9-CARD FEATURES SECTION TAILORED TO FAILURES -->
          {render_features_bento()}

          <!-- 1. FRAMEWORK SECTION (Interactive Code & Invariant Proofs) -->
          <div class="flex items-center gap-4 my-8">
            <span class="text-lg font-medium text-foreground/90 dark:text-foreground/80 tracking-tight shrink-0">Framework</span>
            <div class="flex-1 border-t border-foreground/10"></div>
          </div>
          <p class="text-[14px] sm:text-[15px] text-foreground/70 dark:text-foreground/60 leading-relaxed mb-5 font-normal">
            Compare how raw LLM token prediction generates vulnerable happy-path code versus how Failures MCP enforces deterministic invariants.
          </p>

          <div class="border border-foreground/[0.08] bg-foreground/[0.01] overflow-hidden mb-8">
            <!-- Framework Topbar Tabs -->
            <div class="flex items-center justify-between border-b border-foreground/[0.08] bg-foreground/[0.02] px-3">
              <div class="flex items-center overflow-x-auto">
                <button class="ba-fw-tab active px-4 py-2.5 text-xs font-mono uppercase tracking-wider text-foreground" data-fw-tab="fw-atomicity">01. Atomicity</button>
                <button class="ba-fw-tab px-4 py-2.5 text-xs font-mono uppercase tracking-wider text-foreground/50 hover:text-foreground" data-fw-tab="fw-concurrency">02. Concurrency</button>
                <button class="ba-fw-tab px-4 py-2.5 text-xs font-mono uppercase tracking-wider text-foreground/50 hover:text-foreground" data-fw-tab="fw-ordering">03. Ordering</button>
                <button class="ba-fw-tab px-4 py-2.5 text-xs font-mono uppercase tracking-wider text-foreground/50 hover:text-foreground" data-fw-tab="fw-timeout">04. Timeout</button>
              </div>
              <span class="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-mono text-foreground/40 pr-2">
                <span class="size-1.5 rounded-full bg-emerald-500"></span> AST INVARIANT PROOF
              </span>
            </div>

            <!-- Tab 1: Atomicity -->
            <div id="fw-atomicity" class="ba-fw-pane active p-4 sm:p-5">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="p-4/20 bg-red-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-red-500/10">
                    <span class="text-[11px] font-mono text-red-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Naive LLM Generation</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">checkout.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>async def process_checkout(user_id, amount):
    # Charge external API before DB transaction!
    charge = await stripe.charge(amount=amount)
    await db.execute(
        "INSERT INTO orders (user_id, status) VALUES (%s, 'paid')",
        user_id
    )
    return {{"order_id": charge.id}}</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-red-500/10 flex items-start gap-2 text-[11px] font-mono text-red-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> CRITICAL:</span></span>
                    <span>Network partition or crash leaves customer billed with zero order created in Postgres.</span>
                  </div>
                </div>

                <div class="p-4 border border-emerald-500/20 bg-emerald-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-emerald-500/10">
                    <span class="text-[11px] font-mono text-emerald-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Failures MCP Verified</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">checkout_safe.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>async def process_checkout(user_id, amount, idem_key):
    # 1. State written as 'pending' inside DB transaction
    async with db.transaction() as tx:
        order = await tx.execute(
            "INSERT INTO orders (user_id, amount, status, idem_key) VALUES (%s, %s, 'pending', %s) RETURNING id",
            user_id, amount, idem_key
        )
    # 2. External side effect with provider idempotency key
    charge = await stripe.charge(amount=amount, idempotency_key=idem_key)
    await db.execute(
        "UPDATE orders SET status = 'confirmed', charge_id = %s WHERE id = %s",
        charge.id, order.id
    )</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-emerald-500/10 flex items-start gap-2 text-[11px] font-mono text-emerald-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> INVARIANT:</span></span>
                    <span>Pending state + provider idempotency guarantees safe reconciliation under all crash scenarios.</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab 2: Concurrency -->
            <div id="fw-concurrency" class="ba-fw-pane p-4 sm:p-5">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="p-4/20 bg-red-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-red-500/10">
                    <span class="text-[11px] font-mono text-red-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Naive LLM Generation</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">inventory.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>async def buy_ticket(event_id):
    # Unsafe read-modify-write!
    event = await db.fetch_one("SELECT seats FROM events WHERE id = %s", event_id)
    if event['seats'] > 0:
        await db.execute("UPDATE events SET seats = %s WHERE id = %s", event['seats'] - 1, event_id)</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-red-500/10 flex items-start gap-2 text-[11px] font-mono text-red-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> CRITICAL:</span></span>
                    <span>Race condition: 50 concurrent requests see seats=1 and all decrement, resulting in massive overselling.</span>
                  </div>
                </div>

                <div class="p-4 border border-emerald-500/20 bg-emerald-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-emerald-500/10">
                    <span class="text-[11px] font-mono text-emerald-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Failures MCP Verified</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">inventory_locked.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>async def buy_ticket(event_id):
    # Atomic conditional update with version lock
    res = await db.execute(
        "UPDATE events SET seats = seats - 1, version = version + 1 "
        "WHERE id = %s AND seats > 0",
        event_id
    )
    if res.rows_affected == 0:
        raise HTTPException(409, "Seats sold out or concurrent conflict")</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-emerald-500/10 flex items-start gap-2 text-[11px] font-mono text-emerald-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> INVARIANT:</span></span>
                    <span>Optimistic concurrency control guarantees zero overselling regardless of request volume.</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab 3: Ordering -->
            <div id="fw-ordering" class="ba-fw-pane p-4 sm:p-5">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="p-4/20 bg-red-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-red-500/10">
                    <span class="text-[11px] font-mono text-red-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Naive LLM Generation</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">webhook.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>@app.post("/webhooks")
async def handle_sub(e: Event):
    # Blind state overwrite!
    await db.execute(
        "UPDATE subscriptions SET status = %s WHERE id = %s",
        e.status, e.sub_id
    )</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-red-500/10 flex items-start gap-2 text-[11px] font-mono text-red-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> CRITICAL:</span></span>
                    <span>Delayed retry of 'created' event arrives after 'cancelled', wrongly re-activating user account.</span>
                  </div>
                </div>

                <div class="p-4 border border-emerald-500/20 bg-emerald-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-emerald-500/10">
                    <span class="text-[11px] font-mono text-emerald-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Failures MCP Verified</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">webhook_ordered.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>@app.post("/webhooks")
async def handle_sub(e: Event):
    # Monotonic timestamp guard
    await db.execute(
        "UPDATE subscriptions SET status = %s, last_ts = %s "
        "WHERE id = %s AND last_ts < %s",
        e.status, e.ts, e.sub_id, e.ts
    )</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-emerald-500/10 flex items-start gap-2 text-[11px] font-mono text-emerald-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> INVARIANT:</span></span>
                    <span>Monotonic sequence checking guarantees stale deliveries are safely dropped without corruption.</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab 4: Timeout -->
            <div id="fw-timeout" class="ba-fw-pane p-4 sm:p-5">
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="p-4/20 bg-red-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-red-500/10">
                    <span class="text-[11px] font-mono text-red-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Naive LLM Generation</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">gateway.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>async def send_payment(amount):
    try:
        return await http.post("/charge", json={{"amt": amount}})
    except TimeoutException:
        # Blind retry on timeout!
        return await http.post("/charge", json={{"amt": amount}})</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-red-500/10 flex items-start gap-2 text-[11px] font-mono text-red-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> CRITICAL:</span></span>
                    <span>Ambiguous timeout: The original request succeeded at gateway; retry performs a duplicate debit.</span>
                  </div>
                </div>

                <div class="p-4 border border-emerald-500/20 bg-emerald-500/[0.02] rounded-md">
                  <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-emerald-500/10">
                    <span class="text-[11px] font-mono text-emerald-400 font-semibold tracking-wide"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Failures MCP Verified</span></span>
                    <span class="text-[10px] font-mono text-foreground/40">gateway_reconcile.py</span>
                  </div>
                  <pre class="font-mono text-[11px] leading-relaxed text-foreground/80 overflow-x-auto"><code>async def send_payment(amount, op_id):
    try:
        return await http.post("/charge", json={{"amt": amount}}, headers={{"Idempotency-Key": op_id}})
    except (TimeoutException, NetworkError):
        # Explicit status reconciliation before any retry
        return await reconcile_transaction_status(op_id)</code></pre>
                  <div class="mt-3 pt-2.5 border-t border-emerald-500/10 flex items-start gap-2 text-[11px] font-mono text-emerald-400/90 leading-tight">
                    <span class="shrink-0 font-bold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> INVARIANT:</span></span>
                    <span>Ambiguity reconciliation protocol guarantees strictly-once financial transactions.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 1.5 KNOWLEDGE GRAPH — Principles → Failure Modes → Patterns → Tests -->
          <div class="flex items-center gap-4 my-8">
            <span class="text-lg font-medium text-foreground/90 dark:text-foreground/80 tracking-tight shrink-0">Knowledge Graph</span>
            <div class="flex-1 border-t border-foreground/10"></div>
            <span class="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-mono text-foreground/40"><span class="size-1.5 rounded-full bg-emerald-500"></span> 50+ failure modes → 11 invariants</span>
          </div>
          <div class="relative overflow-hidden border border-dashed border-foreground/[0.08] bg-foreground/[0.01] p-4 sm:p-5 mb-8">
            <div class="absolute inset-0 pointer-events-none opacity-15" style="background-image:radial-gradient(circle, currentColor 1px, transparent 1px);background-size:9px 9px;"></div>
            <div class="relative flex items-center justify-between gap-4 mb-4">
              <div class="flex items-center gap-2">
                <span class="text-[11px] font-mono font-semibold uppercase tracking-widest text-foreground/70">Failure rate under chaos</span>
                <span class="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-foreground/40"><span class="size-1.5 rounded-full bg-red-400"></span> without MCP <span class="size-1.5 rounded-full bg-emerald-400 ml-2"></span> with MCP</span>
              </div>
              <span class="text-[10px] font-mono text-foreground/35">24 adversarial scenarios</span>
            </div>
            <svg viewBox="0 0 640 84" class="relative w-full h-[84px] overflow-visible" preserveAspectRatio="none" aria-hidden="true">
              <g stroke="currentColor" stroke-opacity="0.06" stroke-width="0.7"><line x1="0" y1="21" x2="640" y2="21"/><line x1="0" y1="42" x2="640" y2="42"/><line x1="0" y1="63" x2="640" y2="63"/><line x1="160" y1="0" x2="160" y2="84"/><line x1="320" y1="0" x2="320" y2="84"/><line x1="480" y1="0" x2="480" y2="84"/></g>
              <path d="M 0 62 L 40 58 L 80 64 L 120 52 L 160 66 L 200 48 L 240 58 L 280 54 L 320 62 L 360 44 L 400 52 L 440 38 L 480 46 L 520 32 L 560 42 L 600 28 L 640 30" fill="none" stroke="#ef4444" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>
              <path d="M 0 62 L 40 58 L 80 42 L 120 28 L 160 22 L 200 18 L 240 16 L 280 14 L 320 12 L 360 12 L 400 11 L 480 10 L 560 10 L 640 10" fill="none" stroke="#10b981" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/>
              <rect x="118" y="4" width="84" height="58" rx="6" fill="#ef4444" fill-opacity="0.04" stroke="#ef4444" stroke-opacity="0.12" stroke-dasharray="4 3"/>
              <text x="122" y="14" font-family="Geist Mono, monospace" font-size="7" fill="currentColor" opacity="0.45">AMOUNT MISMATCH → RECONCILE</text>
              <circle cx="200" cy="48" r="2.8" fill="#ef4444" stroke="white" stroke-width="1.1"/><circle cx="200" cy="18" r="2.8" fill="#10b981" stroke="white" stroke-width="1.1"/>
              <g font-family="Geist Mono, monospace" font-size="6.5"><text x="208" y="51" fill="#ef4444" opacity="0.9">3 critical</text><text x="208" y="21" fill="#10b981" opacity="0.9">0 critical</text></g>
            </svg>
            <div class="relative flex flex-wrap gap-1.5 mt-4">
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono/15 bg-red-500/5 text-red-400"><span class="size-1 rounded-full bg-red-400"></span>atomicity</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono/15 bg-red-500/5 text-red-400"><span class="size-1 rounded-full bg-red-400"></span>idempotency</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono/15 bg-red-500/5 text-red-400"><span class="size-1 rounded-full bg-red-400"></span>timeout</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono border border-amber-500/15 bg-amber-500/5 text-amber-500"><span class="size-1 rounded-full bg-amber-400"></span>concurrency</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono border border-amber-500/15 bg-amber-500/5 text-amber-500"><span class="size-1 rounded-full bg-amber-400"></span>retry</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono border border-amber-500/15 bg-amber-500/5 text-amber-500"><span class="size-1 rounded-full bg-amber-400"></span>availability</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono border border-amber-500/15 bg-amber-500/5 text-amber-500"><span class="size-1 rounded-full bg-amber-400"></span>ordering</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono/15 bg-blue-500/5 text-blue-400"><span class="size-1 rounded-full bg-blue-400"></span>consistency</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono border border-amber-500/15 bg-amber-500/5 text-amber-500"><span class="size-1 rounded-full bg-amber-400"></span>resource</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono/15 bg-blue-500/5 text-blue-400"><span class="size-1 rounded-full bg-blue-400"></span>recovery</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono/15 bg-blue-500/5 text-blue-400"><span class="size-1 rounded-full bg-blue-400"></span>observability</span>
              <span class="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono border border-dashed border-foreground/15 bg-foreground/[0.02] text-foreground/50">+ 50 failure modes</span>
            </div>
            <div class="relative mt-3 flex items-center justify-between text-[10px] font-mono text-foreground/35">
              <span>Principles → Failure modes → Patterns (idempotency-key, outbox, breaker) → Tests</span>
              <a href="docs/index.html" class="text-foreground/60 hover:text-foreground underline decoration-dotted underline-offset-2">explore graph →</a>
            </div>
          </div>

          <!-- 2. INFRASTRUCTURE SECTION (Authentic Dashed Cards & Radial Gradients) -->
          <div class="flex items-center gap-4 my-8">
            <span class="text-lg font-medium text-foreground/90 dark:text-foreground/80 tracking-tight shrink-0">Infrastructure</span>
            <div class="flex-1 border-t border-foreground/10"></div>
          </div>
          <p class="text-[14px] sm:text-[15px] text-foreground/70 dark:text-foreground/60 leading-relaxed mb-5 font-normal">
            Connect to Failures MCP and power your autonomous development workflows with deterministic AST verification, chaos simulations, and benchmark metrics.
          </p>

          <div class="relative z-10 grid grid-cols-3 gap-px bg-foreground/[0.08] border border-dashed border-foreground/[0.08] overflow-x-auto mt-4 mb-8">
            <!-- Card 1 -->
            <div class="relative overflow-hidden p-4 bg-background min-w-0">
              <div class="absolute inset-0 pointer-events-none opacity-20" style="background-image:radial-gradient(circle, currentColor 1px, transparent 1px);background-size:8px 8px;"></div>
              <h4 class="relative text-[11px] sm:text-xs font-mono font-semibold uppercase tracking-widest text-foreground/90 dark:text-foreground/75 mb-3 flex items-center gap-2">
                {COMPANY_LOGOS['postgres']}
                <span>AST Engine</span>
              </h4>
              <ul class="space-y-2 relative">
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Abstract syntax tree traversal</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Confidence calibration (0.0 to 1.0)</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Line evidence extraction</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Zero hallucination guarantee</span></li>
              </ul>
            </div>

            <!-- Card 2 -->
            <div class="relative overflow-hidden p-4 bg-background min-w-0">
              <div class="absolute inset-0 pointer-events-none opacity-20" style="background-image:radial-gradient(circle, currentColor 1px, transparent 1px);background-size:8px 8px;"></div>
              <h4 class="relative text-[11px] sm:text-xs font-mono font-semibold uppercase tracking-widest text-foreground/90 dark:text-foreground/75 mb-3 flex items-center gap-2">
                {COMPANY_LOGOS['stripe']}
                <span>Chaos Suite</span>
              </h4>
              <ul class="space-y-2 relative">
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Automated Pytest / Jest generation</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Crash-between-writes simulation</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Ambiguous network timeout injection</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>24 Golden benchmark scenarios</span></li>
              </ul>
            </div>

            <!-- Card 3 -->
            <div class="relative overflow-hidden p-4 bg-background min-w-0">
              <div class="absolute inset-0 pointer-events-none opacity-20" style="background-image:radial-gradient(circle, currentColor 1px, transparent 1px);background-size:8px 8px;"></div>
              <h4 class="relative text-[11px] sm:text-xs font-mono font-semibold uppercase tracking-widest text-foreground/90 dark:text-foreground/75 mb-3 flex items-center gap-2">
                {COMPANY_LOGOS['supabase']}
                <span>11 Invariants</span>
              </h4>
              <ul class="space-y-2 relative">
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Transactional outbox pattern</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Optimistic locking with versioning</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Monotonic message deduplication</span></li>
                <li class="flex items-start gap-2 text-[13px] text-foreground/70 dark:text-foreground/55"><span class="text-foreground/35 mt-0.5 font-mono text-[11px] select-none shrink-0">+</span><span>Circuit breaker with fail-fast state</span></li>
              </ul>
            </div>
          </div>

          <!-- 3. BENCHMARK — Better Auth Dashed + Trend (real project data) -->
          <div class="flex items-center gap-4 my-8">
            <span class="text-lg font-medium text-foreground/90 dark:text-foreground/80 tracking-tight shrink-0">Benchmark</span>
            <div class="flex-1 border-t border-foreground/10"></div>
            <span class="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 border border-emerald-500/15 bg-emerald-500/5 text-emerald-400"><span class="size-1.5 rounded-full bg-emerald-400 animate-pulse"></span> 100% deterministic</span>
          </div>
          <div class="relative overflow-hidden border border-dashed border-foreground/[0.08] bg-foreground/[0.01] mb-8">
            <div class="absolute inset-0 pointer-events-none opacity-[0.12]" style="background-image:radial-gradient(circle, currentColor 1px, transparent 1px);background-size:9px 9px;"></div>
            <div class="relative p-4 sm:p-5 border-b border-dashed border-foreground/[0.08]">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <p class="text-[13px] text-foreground/70 leading-snug">Deterministic AST engine — tested against <span class="text-foreground font-medium">24</span> adversarial scenarios across <span class="text-foreground">payments, inventory, webhooks, uploads, queues</span> + <span class="text-foreground">6</span> live agent evaluations.</p>
                <span class="inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 border border-foreground/[0.08] bg-background">24 adv • 11 dims • 13 tools</span>
              </div>
              <svg viewBox="0 0 640 48" class="w-full h-[48px] mt-3 overflow-visible" preserveAspectRatio="none" aria-hidden="true">
                <g stroke="currentColor" stroke-opacity="0.06" stroke-width="0.7"><line x1="0" y1="12" x2="640" y2="12"/><line x1="0" y1="24" x2="640" y2="24"/><line x1="0" y1="36" x2="640" y2="36"/></g>
                <path d="M 0 32 L 40 30 L 80 28 L 120 18 L 160 14 L 200 10 L 240 10 L 320 8 L 480 8 L 640 8" fill="none" stroke="#10b981" stroke-width="1.6" stroke-linecap="round" opacity="0.9"/>
                <path d="M 0 32 L 40 30 L 80 34 L 120 28 L 160 30 L 200 26 L 280 22 L 360 18 L 480 14 L 640 10" fill="none" stroke="#ef4444" stroke-width="1.3" stroke-linecap="round" opacity="0.32" stroke-dasharray="3 4"/>
              </svg>
              <div class="flex flex-wrap items-center gap-3 text-[10px] font-mono text-foreground/40 mt-1">
                <span class="flex items-center gap-1"><span class="size-1.5 rounded-full bg-red-400"></span> naive</span>
                <span class="flex items-center gap-1"><span class="size-1.5 rounded-full bg-emerald-400"></span> with MCP</span>
                <span class="hidden sm:inline">payment 3 CRITICAL → 0 • queue +DLQ</span>
                <span class="ml-auto">reproduce: <code>python examples/run_benchmark.py</code> · <a class="underline decoration-dotted underline-offset-2 hover:text-foreground" href="docs/examples.html">harness</a> · <a class="underline decoration-dotted underline-offset-2 hover:text-foreground" href="https://github.com/mayowa-kalejaiye/Failures/tree/main/evaluation/adversarial">cases</a></span>
              </div>
            </div>
            <div class="relative grid grid-cols-2 sm:grid-cols-4 gap-px bg-foreground/[0.08]">
              <div class="bg-background p-4">
                <div class="flex items-center gap-1.5 text-[10px] font-mono text-foreground/40 tracking-wide">DETECTION <span class="size-1 rounded-full bg-emerald-400"></span></div>
                <div class="text-2xl font-bold font-mono text-emerald-400 mt-1">100%</div>
                <div class="text-[11px] text-foreground/50 font-mono mt-0.5">24 / 24 adversarial</div>
                <div class="mt-2 flex gap-1"><span class="h-1 flex-1 bg-emerald-400/20"><span class="block h-full w-full bg-emerald-400"></span></span><span class="h-1 flex-1 bg-emerald-400/20"><span class="block h-full w-full bg-emerald-400"></span></span><span class="h-1 flex-1 bg-emerald-400/20"><span class="block h-full w-full bg-emerald-400"></span></span><span class="h-1 flex-1 bg-emerald-400/20"><span class="block h-full w-full bg-emerald-400"></span></span></div>
              </div>
              <div class="bg-background p-4">
                <div class="flex items-center gap-1.5 text-[10px] font-mono text-foreground/40 tracking-wide">TOOLS <span class="size-1 rounded-full bg-purple-400"></span></div>
                <div class="text-2xl font-bold font-mono text-foreground">13</div>
                <div class="text-[11px] text-foreground/50 font-mono mt-0.5">review_code • check_invariant …</div>
                <div class="mt-2 flex items-center gap-1 text-[10px] font-mono text-foreground/35"><span class="px-1.5 py-0.5 border border-foreground/10 bg-foreground/[0.02]">MCP</span><span class="px-1.5 py-0.5 border border-foreground/10 bg-foreground/[0.02]">STDIO</span></div>
              </div>
              <div class="bg-background p-4">
                <div class="flex items-center gap-1.5 text-[10px] font-mono text-foreground/40 tracking-wide">COST <span class="size-1 rounded-full bg-purple-400"></span></div>
                <div class="text-2xl font-bold font-mono text-purple-400">0 ms</div>
                <div class="text-[11px] text-foreground/50 font-mono mt-0.5">AST, no tokens</div>
                <div class="mt-2 text-[10px] font-mono text-foreground/30">no hallucination</div>
              </div>
              <div class="bg-background p-4">
                <div class="flex items-center gap-1.5 text-[10px] font-mono text-foreground/40 tracking-wide">DIMENSIONS <span class="size-1 rounded-full bg-amber-400"></span></div>
                <div class="text-2xl font-bold font-mono text-amber-400">11 / 11</div>
                <div class="text-[11px] text-foreground/50 font-mono mt-0.5">atomicity → observability</div>
                <div class="mt-2 flex flex-wrap gap-1"><span class="text-[8px] font-mono px-1 py-0.5 bg-red-500/5 border border-red-500/10 text-red-400">CRIT 3</span><span class="text-[8px] font-mono px-1 py-0.5 bg-amber-500/5 border border-amber-500/10 text-amber-400">HIGH 5</span><span class="text-[8px] font-mono px-1 py-0.5 bg-blue-500/5 border border-blue-500/10 text-blue-400">MED 3</span></div>
              </div>
            </div>
            <div class="relative grid grid-cols-1 sm:grid-cols-3 gap-px bg-foreground/[0.08] border-t border-foreground/[0.08]">
              <div class="bg-background p-3 flex items-center justify-between"><span class="text-[11px] font-mono text-foreground/60">payment</span><span class="text-[11px] font-mono"><span class="text-red-400">3 →</span> <span class="text-emerald-400">0 CRIT</span></span></div>
              <div class="bg-background p-3 flex items-center justify-between"><span class="text-[11px] font-mono text-foreground/60">queue</span><span class="text-[11px] font-mono"><span class="text-red-400">1 →</span> <span class="text-emerald-400">0 CRIT</span> <span class="text-foreground/30">+ DLQ</span></span></div>
              <div class="bg-background p-3 flex items-center justify-between"><span class="text-[11px] font-mono text-foreground/60">patterns</span><span class="text-[11px] font-mono text-foreground/50">outbox • breaker • lock</span></div>
            </div>
          </div>


          <!-- 4. FAQ — Better Auth Dashed Accordion -->
          <div class="flex items-center gap-4 my-8">
            <span class="text-lg font-medium text-foreground/90 dark:text-foreground/80 tracking-tight shrink-0">Frequently Asked Questions</span>
            <div class="flex-1 border-t border-foreground/10"></div>
          </div>
          <div class="flex flex-col gap-px bg-foreground/[0.08] border border-dashed border-foreground/[0.08] overflow-hidden mb-12">
            <div class="ba-faq-item group relative bg-background hover:bg-foreground/[0.01] transition-colors" data-faq>
              <button class="ba-faq-trigger w-full flex items-center justify-between gap-4 p-4 text-left">
                <span class="flex items-center gap-3">
                  <span class="hidden sm:inline-flex size-6 items-center justify-center border border-dashed border-foreground/15 bg-foreground/[0.02] text-[10px] font-mono text-foreground/40">01</span>
                  <span class="text-[13px] font-medium text-foreground/90">Why do AI coding agents need Failures MCP?</span>
                </span>
                <span class="ba-faq-icon flex size-6 items-center justify-center border border-foreground/10 bg-background text-foreground/40 transition-transform transition-transform">+</span>
              </button>
              <div class="ba-faq-content px-4 pb-4 pt-0">
                <p class="text-[13px] leading-relaxed text-foreground/70 border-t border-dashed border-foreground/[0.06] pt-3">LLMs learn from tutorials that only show the happy path. They charge Stripe before writing to Postgres, retry without idempotency, and read-modify-write without locks. Failures gives agents 11 deterministic invariants — checked via AST, not prompts — so failures are caught before deploy.</p>
              </div>
            </div>
            <div class="ba-faq-item group relative bg-background hover:bg-foreground/[0.01] transition-colors" data-faq>
              <button class="ba-faq-trigger w-full flex items-center justify-between gap-4 p-4 text-left">
                <span class="flex items-center gap-3">
                  <span class="hidden sm:inline-flex size-6 items-center justify-center border border-dashed border-foreground/15 bg-foreground/[0.02] text-[10px] font-mono text-foreground/40">02</span>
                  <span class="text-[13px] font-medium text-foreground/90">Is Failures just another LLM prompt?</span>
                </span>
                <span class="ba-faq-icon flex size-6 items-center justify-center border border-foreground/10 bg-background text-foreground/40 transition-transform transition-transform">+</span>
              </button>
              <div class="ba-faq-content px-4 pb-4 pt-0">
                <p class="text-[13px] leading-relaxed text-foreground/70 border-t border-dashed border-foreground/[0.06] pt-3">No. <code>review_code</code> parses your file to an AST, extracts evidence (<code>stripe.charge</code> without <code>idempotency_key</code>), and returns <code>Confidence: 0.91 [CRITICAL]</code> with line evidence. No tokens, no hallucination — <code>0.0 ms</code> AST cost for 24 adversarial tests.</p>
              </div>
            </div>
            <div class="ba-faq-item group relative bg-background hover:bg-foreground/[0.01] transition-colors" data-faq>
              <button class="ba-faq-trigger w-full flex items-center justify-between gap-4 p-4 text-left">
                <span class="flex items-center gap-3">
                  <span class="hidden sm:inline-flex size-6 items-center justify-center border border-dashed border-foreground/15 bg-foreground/[0.02] text-[10px] font-mono text-foreground/40">03</span>
                  <span class="text-[13px] font-medium text-foreground/90">How do I install with Claude Code / Cursor?</span>
                </span>
                <span class="ba-faq-icon flex size-6 items-center justify-center border border-foreground/10 bg-background text-foreground/40 transition-transform transition-transform">+</span>
              </button>
              <div class="ba-faq-content px-4 pb-4 pt-0">
                <p class="text-[13px] leading-relaxed text-foreground/70 border-t border-dashed border-foreground/[0.06] pt-3">Add to <code>claude_desktop_config.json</code> or Cursor MCP: <code>{{"failures": {{"command": "failures-mcp", "args": []}}}}</code> (after <code>pipx install failures-mcp</code>). Your agent gets 13 tools: <code>review_plan</code>, <code>check_invariant</code>, <code>generate_failure_tests</code> and 10 more — all deterministic.</p>
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>
  </div>

  {render_search_dialog()}

  <script src="js/main.js"></script>
</body>
</html>"""

    (BASE_DIR / "index.html").write_text(html, encoding="utf-8")
    print("✓ Built exact Better Auth landing page with rich Failures content: website/index.html")

def build_docs_pages():
    def make_sidebar(active_id, depth):
        root_rel = "../" * depth
        docs_rel = f"{root_rel}docs/"
        principle_rel = f"{docs_rel}principles/"

        principle_links = []
        for p in PRINCIPLES:
            act = " active" if active_id == p['id'] else ""
            principle_links.append(f"""      <a href="{principle_rel}{p['id']}.html" class="ba-sidebar-link{act}">
        <span>{p['name']}</span>
        <span class="ba-dot {p['dot']}"></span>
      </a>""")

        return f"""<aside class="ba-docs-sidebar">
  <div class="ba-sidebar-group">
    <div class="ba-sidebar-label">Getting Started</div>
    <a href="{docs_rel}index.html" class="ba-sidebar-link{' active' if active_id == 'intro' else ''}">
      <span>Introduction</span>
    </a>
  </div>

  <div class="ba-sidebar-group">
    <div class="ba-sidebar-label">Principles ({len(PRINCIPLES)})</div>
{chr(10).join(principle_links)}
  </div>

  <div class="ba-sidebar-group">
    <div class="ba-sidebar-label">Labs</div>
    <a href="{docs_rel}labs/index.html" class="ba-sidebar-link{' active' if active_id == 'lab-index' else ''}">
      <span>Interactive Labs</span>
    </a>
    <a href="{docs_rel}labs/payment.html" class="ba-sidebar-link{' active' if active_id == 'lab-payment' else ''}">
      <span>Payment Lab</span>
    </a>
    <a href="{docs_rel}labs/queue.html" class="ba-sidebar-link{' active' if active_id == 'lab-queue' else ''}">
      <span>Queue Lab</span>
    </a>
    <a href="{docs_rel}labs/retry.html" class="ba-sidebar-link{' active' if active_id == 'lab-retry' else ''}">
      <span>Retry Lab</span>
    </a>
  </div>

  <div class="ba-sidebar-group">
    <div class="ba-sidebar-label">Reference</div>
    <a href="{docs_rel}tools.html" class="ba-sidebar-link{' active' if active_id == 'tools' else ''}">
      <span>Tools Reference</span>
    </a>
    <a href="{docs_rel}patterns.html" class="ba-sidebar-link{' active' if active_id == 'patterns' else ''}">
      <span>Patterns Catalog</span>
    </a>
    <a href="{docs_rel}examples.html" class="ba-sidebar-link{' active' if active_id == 'examples' else ''}">
      <span>Benchmark &amp; Examples</span>
    </a>
  </div>
</aside>"""

    # 1. Docs Intro
    intro_toc = [
        ("what-is-failures", "What is Failures?"),
        ("the-problem", "The Problem with AI Code"),
        ("deterministic-guarantees", "Deterministic Guarantees"),
        ("principles-overview", "Principles Overview")
    ]
    intro_toc_html = chr(10).join([f'<a href="#{tid}" class="ba-toc-link">{tlabel}</a>' for tid, tlabel in intro_toc])

    intro_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Introduction | Failures Docs</title>
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
    .ba-landing .lg\:w-\[60\%] {{
      scroll-margin-top: 80px;
    }}
    @media (min-width: 1024px) {{
      .ba-landing .lg\:w-\[60\%] {{
        padding-top: 40px;
      }}
    }}
    .ba-readme-header {{
      padding-top: 32px;
      scroll-margin-top: 80px;
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body>
  {render_topbar(active_tab="docs", depth=1)}

  <div class="ba-docs-layout" style="padding-top:45px;">
    {make_sidebar("intro", depth=1)}

    <main class="ba-docs-content ba-prose">
      <div class="ba-doc-meta-row">
        <div class="ba-breadcrumb">
          <a href="../index.html">Home</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>Docs</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>Introduction</span>
        </div>
        <div class="ba-doc-actions">
          <button class="ba-pill-btn copy-btn" data-copy="doc-body"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy MD</button>
        </div>
      </div>

      <div id="doc-body">
        <h1>Introduction</h1>
        <p class="ba-lead">A field manual for the part most tutorials skip: what happens when the network drops, the database crashes between two writes, or the same request arrives twice. Each of the 11 principles is a self-contained walkthrough — why the failure exists, how the machinery works underneath, and runnable Python and Go you can paste and run.</p>

        <div class="ba-callout ba-callout-danger">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <div>
            <strong>The network will fail. The question is what your code does next.</strong> Not if, but when — a timeout hides whether the charge succeeded, a retry arrives twice, a crash lands between two writes. A good system does not pretend these do not happen; it makes them predictable.
          </div>
        </div>

        <h2 id="what-is-failures">What is Failures?</h2>
        <p>Failures is a reference, not a framework. It documents 11 invariants — atomicity, idempotency, timeout, and so on — as the machinery underneath, the way <em>Backend from First Principles</em> does for HTTP or TCP. Each invariant is a short field manual: why the failure exists in the first place, how the database or the queue actually behaves underneath, and the pattern that makes it safe. The same chapter runs in Python and Go, grounded in how Postgres, Redis, and Stripe actually work.</p>
        <p>For coding agents, Failures ships as an MCP server. Your agent does not get a longer prompt; it gets a tool that parses code to an AST and checks the invariant against it. Not “does this look good?” but “if the client retries this exact request, do we have a <code>UNIQUE(key)</code> to catch it and a cached response to return?” The answer is a line number, a confidence, and the test that would have caught it — no hallucination.</p>

        <h2 id="the-problem">The Problem with Happy-Path Code</h2>
        <p>Most backend examples end at the happy path: the 200 OK that returns while the network is stable. In production, the happy path is the exception. A model trained on those examples will generate an endpoint that:</p>
        <ul>
          <li>Charges an external payment provider before writing to the database.</li>
          <li>Retries non-idempotent endpoints upon network timeouts, causing double charges.</li>
          <li>Performs read-modify-write queries without locks, creating race conditions.</li>
          <li>Leaves workers hanging without timeouts, exhausting connection pools.</li>
        </ul>

        <h2 id="deterministic-guarantees">How a Check Works</h2>
        <p>Every check is a static rule, not a guess. Give the MCP a function, it builds the AST, finds <code>await stripe.charge</code> without a preceding <code>SELECT ... WHERE key = ?</code> and <code>UNIQUE</code>, and returns the exact lines with a calibrated confidence (<code>0.91 [CRITICAL]</code>). It also returns the control that would make it safe — a pending row, an idempotency table, a reconciliation sweep — and the test that proves it, like <code>retry_after_provider_success</code>. The cost is the parse, <code>0.0 ms</code> of tokens, because there is no model call.</p>

        <div class="ba-code-block">
          <div class="ba-code-header">
            <span class="ba-code-title">review_code() Sample Output</span>
            <button class="ba-pill-btn copy-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</button>
          </div>
          <pre><code>STATIC FAILURE CHECK — Code Review

[CRITICAL] External side-effect without idempotency key (idempotency) Confidence: 0.91 [STATIC FAILURE CHECK]
  Why: Network boundary creates ambiguous outcome; retry may duplicate charge.
  Evidence: await stripe.charge(p.amount)
  Risk: Retry after timeout duplicates charge
  Required: persist idempotency key BEFORE external call, dedup check on retry
  Tests: retry_after_provider_success, duplicate_idempotency_key</code></pre>
        </div>

        <h2 id="principles-overview">The 11 Principles</h2>
        <p>Every engineering failure mode falls under 11 formal dimensions:</p>
        <div class="ba-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Principle</th>
                <th>Guiding Question</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><a href="principles/atomicity.html">Atomicity</a></td><td>Can operations partially succeed?</td><td><span class="ba-dot critical" style="display:inline-block; margin-right:4px;"></span>CRITICAL</td></tr>
              <tr><td><a href="principles/idempotency.html">Idempotency</a></td><td>What happens if executed twice?</td><td><span class="ba-dot critical" style="display:inline-block; margin-right:4px;"></span>CRITICAL</td></tr>
              <tr><td><a href="principles/timeout.html">Timeout</a></td><td>Did it succeed or fail?</td><td><span class="ba-dot critical" style="display:inline-block; margin-right:4px;"></span>CRITICAL</td></tr>
              <tr><td><a href="principles/concurrency.html">Concurrency</a></td><td>What if 2 actors edit same state?</td><td><span class="ba-dot high" style="display:inline-block; margin-right:4px;"></span>HIGH</td></tr>
              <tr><td><a href="principles/retry-safety.html">Retry Safety</a></td><td>Is it safe to retry?</td><td><span class="ba-dot high" style="display:inline-block; margin-right:4px;"></span>HIGH</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <aside class="ba-docs-toc">
      <div class="ba-toc-title">On this page</div>
      {intro_toc_html}
    </aside>
  </div>

  {render_search_dialog()}
  <script src="../js/main.js"></script>
</body>
</html>"""
    (DOCS_DIR / "index.html").write_text(intro_html, encoding="utf-8")

    # 2. Principle Pages
    for idx, p in enumerate(PRINCIPLES):
        p_toc = [
            ("the-invariant", "The Invariant"),
            ("why-it-happens", "Why It Happens"),
            ("cataloged-failure-modes", "Cataloged Failure Modes"),
            ("code-comparison", "Code Comparison"),
            ("mitigation-patterns", "Mitigation Patterns")
        ]
        p_toc_html = chr(10).join([f'<a href="#{tid}" class="ba-toc-link">{tlabel}</a>' for tid, tlabel in p_toc])

        p_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{p['name']} Principle | Failures Docs</title>
  <link rel="icon" type="image/svg+xml" href="../../favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
    .ba-landing .lg\:w-\[60\%] {{
      scroll-margin-top: 80px;
    }}
    @media (min-width: 1024px) {{
      .ba-landing .lg\:w-\[60\%] {{
        padding-top: 40px;
      }}
    }}
    .ba-readme-header {{
      padding-top: 32px;
      scroll-margin-top: 80px;
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body>
  {render_topbar(active_tab="docs", depth=2)}

  <div class="ba-docs-layout" style="padding-top:45px;">
    {make_sidebar(p['id'], depth=2)}

    <main class="ba-docs-content ba-prose">
      <div class="ba-doc-meta-row">
        <div class="ba-breadcrumb">
          <a href="../../index.html">Home</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <a href="../index.html">Docs</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>{p['name']}</span>
        </div>
        <div class="ba-doc-actions">
          <span class="ba-pill-btn" style="color:var(--{p['dot']}); border-color:var(--{p['dot']});">{p['severity']}</span>
        </div>
      </div>

      <h1>{p['name']}</h1>
      <p class="ba-lead">"{p['question']}"</p>

      <div class="ba-callout ba-callout-{'danger' if p['dot'] == 'critical' else 'warning'}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <div>
          <strong>Invariant:</strong> {p['invariant']}
        </div>
      </div>

      <h2 id="the-invariant">Applies To</h2>
      <p>{', '.join(p['applies_to'])}</p>

      <h2 id="why-it-happens">Why It Happens</h2>
      <p>{p['desc']}</p>
      {PRINCIPLE_VERBOSE.get(p['id'], "")}

      <h2 id="cataloged-failure-modes">Cataloged Failure Modes</h2>
      <ul>
        {''.join([f'<li><code>{m}</code></li>' for m in p['failure_modes']])}
      </ul>

      <h2 id="code-comparison">Code Comparison</h2>
      <div class="flex items-center gap-2 mb-3">
        <span class="text-[11px] font-mono text-foreground/50 mr-2">Language:</span>
        <button class="lang-tab active px-2.5 py-1 text-[11px] font-mono border border-foreground/15 bg-foreground text-background" data-lang="python" onclick="switchLang(this, 'python')">Python</button>
        <button class="lang-tab px-2.5 py-1 text-[11px] font-mono border border-foreground/10 bg-background text-foreground/60 hover:bg-foreground/[0.03]" data-lang="js" onclick="switchLang(this, 'js')">TypeScript</button>
      </div>
      <div class="lang-block lang-python">
      <div class="my-4/20 bg-red-500/[0.02] rounded-md overflow-hidden">
        <div class="flex items-center justify-between px-3 py-2 border-b border-red-500/10 bg-red-500/[0.03]">
          <span class="text-[11px] font-mono text-red-400 font-semibold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Fragile (AI Happy Path) — Python</span></span>
          <span class="text-[10px] font-mono text-foreground/40">{p['id']}_fragile.py</span>
        </div>
        <pre class="p-3.5 font-mono text-[11.5px] leading-relaxed text-foreground/80 overflow-x-auto"><code>{p['code_bad']}</code></pre>
      </div>

      <div class="my-4 border border-emerald-500/20 bg-emerald-500/[0.02] rounded-md overflow-hidden">
        <div class="flex items-center justify-between px-3 py-2 border-b border-emerald-500/10 bg-emerald-500/[0.03]">
          <span class="text-[11px] font-mono text-emerald-400 font-semibold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Resilient (Failures Verified) — Python</span></span>
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-mono text-foreground/40">{p['id']}_safe.py</span>
            <button class="ba-pill-btn copy-btn"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</button>
          </div>
        </div>
        <pre class="p-3.5 font-mono text-[11.5px] leading-relaxed text-foreground/80 overflow-x-auto"><code>{p['code_good']}</code></pre>
      </div>
      </div>
      <div class="lang-block lang-js hidden">
      <div class="my-4/20 bg-red-500/[0.02] rounded-md overflow-hidden">
        <div class="flex items-center justify-between px-3 py-2 border-b border-red-500/10 bg-red-500/[0.03]">
          <span class="text-[11px] font-mono text-red-400 font-semibold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Fragile (AI Happy Path) — TypeScript</span></span>
          <span class="text-[10px] font-mono text-foreground/40">{p['id']}_fragile.ts</span>
        </div>
        <pre class="p-3.5 font-mono text-[11.5px] leading-relaxed text-foreground/80 overflow-x-auto"><code>{p['code_bad_js']}</code></pre>
      </div>

      <div class="my-4 border border-emerald-500/20 bg-emerald-500/[0.02] rounded-md overflow-hidden">
        <div class="flex items-center justify-between px-3 py-2 border-b border-emerald-500/10 bg-emerald-500/[0.03]">
          <span class="text-[11px] font-mono text-emerald-400 font-semibold"><span class="inline-flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Resilient (Failures Verified) — TypeScript</span></span>
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-mono text-foreground/40">{p['id']}_safe.ts</span>
            <button class="ba-pill-btn copy-btn"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</button>
          </div>
        </div>
        <pre class="p-3.5 font-mono text-[11.5px] leading-relaxed text-foreground/80 overflow-x-auto"><code>{p['code_good_js']}</code></pre>
      </div>
      </div>

      <h2 id="mitigation-patterns">Mitigation Patterns</h2>
      <ul>
        {''.join([f'<li><a href="../patterns.html#{pat}"><strong>{pat}</strong></a></li>' for pat in p['patterns']])}
      </ul>
    </main>

    <aside class="ba-docs-toc">
      <div class="ba-toc-title">On this page</div>
      {p_toc_html}
    </aside>
  </div>

  {render_search_dialog()}
  <script src="../../js/main.js"></script>
</body>
</html>"""
        (PRINCIPLES_DIR / f"{p['id']}.html").write_text(p_html, encoding="utf-8")

    # 3. Tools Reference
    tools_toc = [(f"tool-{t['name'].replace('_', '-')}", f"{t['name']}()") for t in TOOLS]
    tools_toc_html = chr(10).join([f'<a href="#{tid}" class="ba-toc-link">{tlabel}</a>' for tid, tlabel in tools_toc])

    tools_blocks = []
    for t in TOOLS:
        t_id = f"tool-{t['name'].replace('_', '-')}"
        params_rows = [f"<tr><td><code>{p[0]}</code></td><td><code>{p[1]}</code></td><td>{p[2]}</td><td>{p[3]}</td></tr>" for p in t['params']]
        tools_blocks.append(f"""<div style="margin-bottom: 48px;" id="{t_id}">
  <h2 style="margin-top:0;"><code>{t['name']}()</code> <span class="ba-pill-btn">{t['badge']}</span></h2>
  <p>{t['desc']}</p>
  
  <div class="ba-table-wrapper">
    <table>
      <thead>
        <tr><th>Parameter</th><th>Type</th><th>Description</th><th>Required</th></tr>
      </thead>
      <tbody>
        {''.join(params_rows)}
      </tbody>
    </table>
  </div>

  <div class="ba-code-block">
    <div class="ba-code-header">
      <span class="ba-code-title">Example Input &amp; Output</span>
      <button class="ba-pill-btn copy-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</button>
    </div>
    <pre><code>// Input
{t['input_example']}

// Output
{t['output_example']}</code></pre>
  </div>
</div>""")

    tools_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tools Reference | Failures Docs</title>
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
    .ba-landing .lg\:w-\[60\%] {{
      scroll-margin-top: 80px;
    }}
    @media (min-width: 1024px) {{
      .ba-landing .lg\:w-\[60\%] {{
        padding-top: 40px;
      }}
    }}
    .ba-readme-header {{
      padding-top: 32px;
      scroll-margin-top: 80px;
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body>
  {render_topbar(active_tab="tools", depth=1)}

  <div class="ba-docs-layout" style="padding-top:45px;">
    {make_sidebar("tools", depth=1)}

    <main class="ba-docs-content ba-prose">
      <div class="ba-doc-meta-row">
        <div class="ba-breadcrumb">
          <a href="../index.html">Home</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <a href="index.html">Docs</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>Tools Reference</span>
        </div>
      </div>

      <h1>Tools Reference</h1>
      <p class="ba-lead">Complete specification for all 12 deterministic Failures MCP tools.</p>

      {''.join(tools_blocks)}
    </main>

    <aside class="ba-docs-toc">
      <div class="ba-toc-title">On this page</div>
      {tools_toc_html}
    </aside>
  </div>

  {render_search_dialog()}
  <script src="../js/main.js"></script>
</body>
</html>"""
    (DOCS_DIR / "tools.html").write_text(tools_html, encoding="utf-8")

    # 4. Patterns Catalog
    patterns_toc = [(p['id'], p['name']) for p in PATTERNS]
    patterns_toc_html = chr(10).join([f'<a href="#{tid}" class="ba-toc-link">{tlabel}</a>' for tid, tlabel in patterns_toc])

    patterns_blocks = []
    for p in PATTERNS:
        patterns_blocks.append(f"""<div style="margin-bottom: 48px;" id="{p['id']}">
  <h2>{p['name']} <span class="ba-pill-btn">{p['badge']}</span></h2>
  <p><strong>Mitigates:</strong> {', '.join(p['principles'])}</p>
  <p>{p['desc']}</p>
  
  <div class="ba-code-block">
    <div class="ba-code-header">
      <span class="ba-code-title">Python Implementation</span>
      <button class="ba-pill-btn copy-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</button>
    </div>
    <pre><code>{p['code']}</code></pre>
  </div>
</div>""")

    patterns_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Patterns Catalog | Failures Docs</title>
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
    .ba-landing .lg\:w-\[60\%] {{
      scroll-margin-top: 80px;
    }}
    @media (min-width: 1024px) {{
      .ba-landing .lg\:w-\[60\%] {{
        padding-top: 40px;
      }}
    }}
    .ba-readme-header {{
      padding-top: 32px;
      scroll-margin-top: 80px;
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body>
  {render_topbar(active_tab="patterns", depth=1)}

  <div class="ba-docs-layout" style="padding-top:45px;">
    {make_sidebar("patterns", depth=1)}

    <main class="ba-docs-content ba-prose">
      <div class="ba-doc-meta-row">
        <div class="ba-breadcrumb">
          <a href="../index.html">Home</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <a href="index.html">Docs</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>Patterns</span>
        </div>
      </div>

      <h1>Engineering Patterns Catalog</h1>
      <p class="ba-lead">Architectural design patterns for surviving distributed network and state failures.</p>

      {''.join(patterns_blocks)}
    </main>

    <aside class="ba-docs-toc">
      <div class="ba-toc-title">On this page</div>
      {patterns_toc_html}
    </aside>
  </div>

  {render_search_dialog()}
  <script src="../js/main.js"></script>
</body>
</html>"""
    (DOCS_DIR / "patterns.html").write_text(patterns_html, encoding="utf-8")

    # 5. Examples & Benchmark
    examples_toc = [
        ("golden-benchmark", "Golden Benchmark"),
        ("before-and-after", "Before & After Refactor"),
        ("automated-runner", "Automated Runner")
    ]
    examples_toc_html = chr(10).join([f'<a href="#{tid}" class="ba-toc-link">{tlabel}</a>' for tid, tlabel in examples_toc])

    examples_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Benchmark &amp; Examples | Failures Docs</title>
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
    .ba-landing .lg\:w-\[60\%] {{
      scroll-margin-top: 80px;
    }}
    @media (min-width: 1024px) {{
      .ba-landing .lg\:w-\[60\%] {{
        padding-top: 40px;
      }}
    }}
    .ba-readme-header {{
      padding-top: 32px;
      scroll-margin-top: 80px;
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body>
  {render_topbar(active_tab="examples", depth=1)}

  <div class="ba-docs-layout" style="padding-top:45px;">
    {make_sidebar("examples", depth=1)}

    <main class="ba-docs-content ba-prose">
      <div class="ba-doc-meta-row">
        <div class="ba-breadcrumb">
          <a href="../index.html">Home</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <a href="index.html">Docs</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>Examples</span>
        </div>
      </div>

      <h1>Golden Benchmark &amp; Examples</h1>
      <p class="ba-lead">Case studies proving deterministic failure detection.</p>

      <h2 id="golden-benchmark">The Golden Benchmark Suite</h2>
      <p>Failures includes a regression benchmark in <code>examples/run_benchmark.py</code>. Naive implementations trigger multiple CRITICAL findings, while improved code reduces findings to zero.</p>

      <h2 id="before-and-after">Before &amp; After Refactor</h2>
      <p><strong>Naive Payment Handler (2 CRITICAL, 2 HIGH):</strong></p>
      <div class="ba-code-block">
        <pre><code>@app.post("/payments")
async def pay(p: Payment):
    res = await stripe.charge(p.amount)
    await db.execute("UPDATE accounts SET bal = bal - %s", p.amount)
    return res</code></pre>
      </div>

      <p><strong>Improved Payment Handler (0 CRITICAL):</strong></p>
      <div class="ba-code-block">
        <div class="ba-code-header">
          <span class="ba-code-title">improved.py</span>
          <button class="ba-pill-btn copy-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy</button>
        </div>
        <pre><code>@app.post("/payments")
async def pay(p: Payment, key: str = Header(...)):
    async with db.transaction() as tx:
        await check_idem(tx, key)
        res = await stripe.charge(p.amount, idempotency_key=key)
        await tx.execute("UPDATE accounts...")
        return res</code></pre>
      </div>

      <h2 id="automated-runner">Running the Benchmark Locally</h2>
      <div class="ba-code-block">
        <pre><code>python examples/run_benchmark.py
# Output: 100% Benchmark Suite Passed. All failure modes correctly identified.</code></pre>
      </div>
    </main>

    <aside class="ba-docs-toc">
      <div class="ba-toc-title">On this page</div>
      {examples_toc_html}
    </aside>
  </div>

  {render_search_dialog()}
  <script src="../js/main.js"></script>
</body>
</html>"""
    (DOCS_DIR / "examples.html").write_text(examples_html, encoding="utf-8")

    # 6. Interactive Labs — same docs shell as every other page
    LABS_DIR.mkdir(parents=True, exist_ok=True)

    def render_labs_page(lab_id, title, lead, toc_items, body_html):
        toc_html = chr(10).join([f'<a href="#{tid}" class="ba-toc-link">{tlabel}</a>' for tid, tlabel in toc_items])
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Failures Docs</title>
  <link rel="icon" type="image/svg+xml" href="../../favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../css/styles.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <script async src="https://www.sabilytics.com/script.js" data-site="6quxsajftis9" data-domain="failures.pxxl.click"></script>
  <style>
    /* Critical nav overrides must load after Tailwind CDN utilities */
    #mobile-nav-drawer {{
      display: none !important;
    }}
    #mobile-nav-drawer.open {{
      display: flex !important;
      flex-direction: column;
    }}
    .ba-desktop-tabs {{
      display: none !important;
    }}
    @media (min-width: 1024px) {{
      #mobile-nav-drawer,
      #mobile-nav-drawer.open {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: none !important;
      }}
      .ba-desktop-tabs {{
        display: flex !important;
      }}
    }}
    @media (max-width: 1023px) {{
      .ba-desktop-tabs {{
        display: none !important;
      }}
      .ba-mobile-nav-btn,
      [data-mobile-toggle] {{
        display: flex !important;
      }}
    }}
  </style>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: 'hsl(var(--background-hsl, 0 0% 100%) / <alpha-value>)',
            foreground: 'hsl(var(--foreground-hsl, 240 10% 3.9%) / <alpha-value>)',
          }},
          fontFamily: {{
            sans: ['Geist', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            mono: ['Geist Mono', 'ui-monospace', 'monospace'],
          }}
        }}
      }}
    }}
  </script>
  <script>
    (function() {{
      const t = localStorage.getItem('failures-theme') || 'system';
      const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) document.documentElement.classList.add('dark');
    }})();
  </script>
</head>
<body>
  {render_topbar(active_tab="docs", depth=2)}

  <div class="ba-docs-layout" style="padding-top:45px;">
    {make_sidebar(lab_id, depth=2)}

    <main class="ba-docs-content ba-prose">
      <div class="ba-doc-meta-row">
        <div class="ba-breadcrumb">
          <a href="../../index.html">Home</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <a href="../index.html">Docs</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <a href="index.html">Labs</a>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          <span>{title}</span>
        </div>
      </div>

      <h1>{title}</h1>
      <p class="ba-lead">{lead}</p>

      {body_html}
    </main>

    <aside class="ba-docs-toc">
      <div class="ba-toc-title">On this page</div>
      {toc_html}
    </aside>
  </div>

  {render_search_dialog()}
  <script src="../../js/main.js"></script>
</body>
</html>"""

    LAB_TRY_IT_HINT = '<div class="my-4 border border-dashed border-foreground/[0.08] bg-foreground/[0.01] p-4"><div class="text-[11px] font-mono text-foreground/50 mb-2">TRY IT — click to inject failure</div>'

    LABS = [
        {
            "id": "index",
            "sidebar": "lab-index",
            "title": "Interactive Labs",
            "lead": "Trigger a failure, watch the invariant hold, then fix it with the pattern. Each lab mirrors a runnable pair in examples/ — run python examples/run_benchmark.py to see naive vs improved scored by the same MCP checks.",
            "toc": [("labs", "The Labs"), ("run-locally", "Run Them Locally")],
            "body": """<h2 id="labs">The Labs</h2>
      <ul>
        <li><a href="payment.html"><strong>Payment</strong></a> — idempotency + reconciliation (see <code>examples/payment/naive.py</code> vs <code>improved.py</code>)</li>
        <li><a href="queue.html"><strong>Queue</strong></a> — ack after + DLQ (see <code>examples/queue/</code>)</li>
        <li><a href="retry.html"><strong>Retry</strong></a> — backoff + jitter (see <code>examples/auth/</code> retry + rate-limit)</li>
      </ul>
      <h2 id="run-locally">Run Them Locally</h2>
      <div class="ba-code-block">
        <pre><code>python examples/run_benchmark.py
# Output: 100% Benchmark Suite Passed. All failure modes correctly identified.</code></pre>
      </div>""",
        },
        {
            "id": "payment",
            "sidebar": "lab-payment",
            "title": "Payment Lab",
            "lead": "Make a payment survive retry, timeout, and crash. Trigger each failure and watch the invariant hold.",
            "toc": [("try-it", "Try It"), ("the-pattern", "The Pattern"), ("run-locally", "Run It Locally")],
            "body": """<h2 id="try-it">Try It</h2>
      """ + LAB_TRY_IT_HINT + """
        <button onclick="document.getElementById('out').textContent='→ retry with same Idempotency-Key → 200 (cached, no second charge) — invariant holds ✓'" class="px-3 py-1.5 bg-foreground text-background text-xs font-mono">Retry after timeout</button>
        <button onclick="document.getElementById('out').textContent='→ duplicate webhook event_id=evt_123 → dedup table hit → 200 already_processed'" class="ml-2 px-3 py-1.5 border border-foreground/15 bg-background text-xs font-mono">Duplicate webhook</button>
        <button onclick="document.getElementById('out').textContent='→ crash after Paystack success before DB commit → pending row remains → reconciler finds it → completes + enrolls'" class="ml-2 px-3 py-1.5 border border-foreground/15 bg-background text-xs font-mono">Crash before persist</button>
        <div id="out" class="mt-3 p-3 bg-background border border-foreground/[0.08] font-mono text-xs min-h-[48px]">Click a button above</div>
      </div>
      <h2 id="the-pattern">The Pattern</h2>
      <p>Persist the idempotency key <em>before</em> the external call, reconcile on timeout instead of blindly retrying. See <a href="../principles/idempotency.html">Idempotency</a> and <a href="../principles/timeout.html">Timeout</a>.</p>
      <div class="ba-code-block">
        <pre><code>await db.execute("INSERT INTO idempotency_keys (key, status) VALUES ($1, 'pending')", [key]);
charge = await paystack.charge({amount}, {idempotencyKey: key}); // timeout?
await db.query("UPDATE idempotency_keys SET status='completed' WHERE key=$1", [key]);</code></pre>
      </div>
      <h2 id="run-locally">Run It Locally</h2>
      <div class="ba-code-block">
        <pre><code>python examples/run_benchmark.py
# payment naive: 3 CRITICAL → improved: 0 CRITICAL</code></pre>
      </div>""",
        },
        {
            "id": "queue",
            "sidebar": "lab-queue",
            "title": "Queue Lab",
            "lead": "Make a worker survive redelivery and poison. Crash before ack and watch dedup save you.",
            "toc": [("try-it", "Try It"), ("the-pattern", "The Pattern"), ("run-locally", "Run It Locally")],
            "body": """<h2 id="try-it">Try It</h2>
      """ + LAB_TRY_IT_HINT + """
        <button onclick="document.getElementById('out').textContent='→ same msg_id=abc delivered twice → dedup table hit → ack without re-send'" class="px-3 py-1.5 bg-foreground text-background text-xs font-mono">Duplicate delivery</button>
        <button onclick="document.getElementById('out').textContent='→ worker crash before ack → message redelivered → processed once via msg_id UNIQUE'" class="ml-2 px-3 py-1.5 border border-foreground/15 bg-background text-xs font-mono">Crash before ack</button>
        <button onclick="document.getElementById('out').textContent='→ poison JSON → 3 fails → moved to DLQ, queue keeps flowing'" class="ml-2 px-3 py-1.5 border border-foreground/15 bg-background text-xs font-mono">Poison message</button>
        <div id="out" class="mt-3 p-3 bg-background border border-foreground/[0.08] font-mono text-xs min-h-[48px]">Click a button above</div>
      </div>
      <h2 id="the-pattern">The Pattern</h2>
      <p>Ack <em>after</em> durable processing, deduplicate on <code>msg_id UNIQUE</code>, route poison to a DLQ after N attempts. See <a href="../principles/recovery.html">Recovery</a>.</p>
      <div class="ba-code-block">
        <pre><code>if (await isDuplicate(msg.id)) { ack(msg); return; }
await process(msg); // idempotent
ack(msg); // AFTER durable work
// on fail: if (attempts>3) dlq.push(msg)</code></pre>
      </div>
      <h2 id="run-locally">Run It Locally</h2>
      <div class="ba-code-block">
        <pre><code>python examples/run_benchmark.py
# queue naive: redelivery duplicates → improved: processed once</code></pre>
      </div>""",
        },
        {
            "id": "retry",
            "sidebar": "lab-retry",
            "title": "Retry Lab",
            "lead": "Turn a retry storm into scattered retries.",
            "toc": [("try-it", "Try It"), ("the-pattern", "The Pattern"), ("run-locally", "Run It Locally")],
            "body": """<h2 id="try-it">Try It</h2>
      """ + LAB_TRY_IT_HINT + """
        <button onclick="document.getElementById('out').textContent='→ 100 clients retry at 1s → thundering herd → downstream dies'" class="px-3 py-1.5 bg-foreground text-background text-xs font-mono">No jitter</button>
        <button onclick="document.getElementById('out').textContent='→ same 100 with jitter 0-200ms → retries scatter → downstream survives'" class="ml-2 px-3 py-1.5 border border-foreground/15 bg-background text-xs font-mono">With jitter</button>
        <div id="out" class="mt-3 p-3 bg-background border border-foreground/[0.08] font-mono text-xs min-h-[48px]">Click a button above</div>
      </div>
      <h2 id="the-pattern">The Pattern</h2>
      <p>Exponential backoff with jitter, only on idempotent operations. See <a href="../principles/retry-safety.html">Retry Safety</a>.</p>
      <div class="ba-code-block">
        <pre><code>delay = Math.min(8000, 500 * (2 ** (attempt-1))) + Math.random()*200;
await sleep(delay); // jitter scatters herd</code></pre>
      </div>
      <h2 id="run-locally">Run It Locally</h2>
      <div class="ba-code-block">
        <pre><code>python examples/run_benchmark.py
# retry without idempotency duplicates → with key + backoff: safe</code></pre>
      </div>""",
        },
    ]

    for lab in LABS:
        page = render_labs_page(lab["sidebar"], lab["title"], lab["lead"], lab["toc"], lab["body"])
        (LABS_DIR / f"{lab['id']}.html").write_text(page, encoding="utf-8")

def main():
    print("Compiling exact Better Auth replica with authentic Failures logo and 01-09 Features section...")
    build_landing_page()
    build_docs_pages()
    print("Done! All 20 pages compiled.")

if __name__ == "__main__":
    main()
