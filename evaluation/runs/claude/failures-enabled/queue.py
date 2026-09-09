"""
Failures-enabled queue — same prompt, but built with Failures MCP available.

Prompt: "Build a background job system for sending course completion certificates. When a student completes a course, enqueue a job that generates a PDF certificate via an external service and emails it. Use a queue and worker pool."

MCP was consulted via review_plan / generate_failure_cases / check_invariant.
"""
from fastapi import FastAPI
import queue as q
import requests
import time

app = FastAPI()
job_queue = q.Queue(maxsize=1000)  # bounded
import sqlite3, uuid

# dedup and DLQ tables (simplified)
# - dedup: msg_id UNIQUE
# - dlq: failed jobs after N retries

MAX_RETRIES = 3

@app.post("/complete")
def complete_course(student_id: str, course_id: str):
    msg_id = str(uuid.uuid4())
    # transactional enqueue via outbox pattern (atomic DB + enqueue)
    # here simplified as atomic put with dedup key persisted
    try:
        db_execute("INSERT INTO outbox (msg_id, payload, status) VALUES (?, ?, 'pending')", (msg_id, f"{student_id}:{course_id}"))
        job_queue.put({"msg_id": msg_id, "student_id": student_id, "course_id": course_id, "attempt": 0})
        db_execute("UPDATE outbox SET status='enqueued' WHERE msg_id=?", (msg_id,))
    except Exception:
        # transactional — outbox stays pending for reconciliation
        raise
    return {"queued": True, "msg_id": msg_id}

def worker_loop():
    while True:
        job = job_queue.get()
        msg_id = job["msg_id"]
        try:
            # idempotent consumer: dedup table
            if is_duplicate(msg_id):
                q_ack(job)
                continue
            generate_and_send_idempotent(job)
            q_ack(job)  # ack AFTER durable processing
        except Exception as e:
            attempt = job.get("attempt", 0) + 1
            if attempt >= MAX_RETRIES:
                move_to_dlq(job, str(e))
                q_ack(job)  # ack poision after DLQ so queue doesn't stall
            else:
                job["attempt"] = attempt
                time.sleep(0.1 * (2 ** attempt))  # backoff
                job_queue.put(job)
                q_nack(job)  # negative ack for visibility
        finally:
            job_queue.task_done()

def is_duplicate(msg_id: str) -> bool:
    try:
        db_execute("INSERT INTO dedup (msg_id) VALUES (?)", (msg_id,))
        return False
    except Exception:
        return True

def generate_and_send_idempotent(job):
    msg_id = job["msg_id"]
    # check already sent (idempotent effect)
    if db_fetch("SELECT 1 FROM certificates WHERE msg_id=?", (msg_id,)):
        return
    # external service with timeout and retry budget
    try:
        resp = requests.post("https://pdf.example.com/generate", json=job, timeout=5)
        resp.raise_for_status()
    except requests.Timeout:
        # ambiguous outcome — do not ack, will retry; reconciliation will check external
        raise
    pdf = resp.content
    # idempotent send: dedup on msg_id
    db_execute("INSERT INTO certificates (msg_id, student_id, course_id) VALUES (?, ?, ?) ON CONFLICT DO NOTHING", (msg_id, job["student_id"], job["course_id"]))
    send_email(job["student_id"], pdf, msg_id)

def send_email(student_id, pdf, msg_id):
    # email with idempotency key
    pass

def q_ack(job): pass
def q_nack(job): pass
def move_to_dlq(job, reason): db_execute("INSERT INTO dlq (msg_id, reason) VALUES (?, ?)", (job["msg_id"], reason))
def db_execute(*a, **k): pass
def db_fetch(*a, **k): return None
