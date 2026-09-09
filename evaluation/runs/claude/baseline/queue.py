"""
Baseline queue — built from prompt without Failures MCP.
Prompt: "Build a background job system for sending course completion certificates. When a student completes a course, enqueue a job that generates a PDF certificate via an external service and emails it. Use a queue and worker pool."

No hidden requirements were given.
"""
from fastapi import FastAPI
import queue as q
import requests

app = FastAPI()
job_queue = q.Queue()

@app.post("/complete")
def complete_course(student_id: str, course_id: str):
    # enqueue — no outbox, no dedup
    job_queue.put({"student_id": student_id, "course_id": course_id})
    return {"queued": True}

def worker_loop():
    while True:
        job = job_queue.get()
        # no ack handling — just process
        generate_and_send(job)
        # no ack, no DLQ, no idempotency
        job_queue.task_done()

def generate_and_send(job):
    # external service without timeout
    resp = requests.post("https://pdf.example.com/generate", json=job)
    pdf = resp.content
    # side effect without dedup — duplicate delivery will duplicate email
    import smtplib
    send_email(job["student_id"], pdf)

def send_email(student_id, pdf):
    # placeholder
    pass
