"""
Background jobs for course completion certificates.

When a student completes a course, a job is enqueued. Workers pull jobs,
generate a PDF via an external service, and email the certificate.
"""

import os
import threading
from queue import Queue
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "https://pdf.example.com/generate")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "https://email.example.com/send")
WORKER_COUNT = int(os.getenv("WORKER_COUNT", "4"))

app = FastAPI(title="Certificate Jobs")
job_queue: Queue = Queue()


class CompletionRequest(BaseModel):
    student_id: int
    course_id: int
    student_email: EmailStr
    student_name: str
    course_title: str


class Job(BaseModel):
    student_id: int
    course_id: int
    student_email: EmailStr
    student_name: str
    course_title: str


def generate_certificate_pdf(job: dict) -> bytes:
    response = httpx.post(
        PDF_SERVICE_URL,
        json={
            "student_name": job["student_name"],
            "course_title": job["course_title"],
            "student_id": job["student_id"],
            "course_id": job["course_id"],
        },
    )
    response.raise_for_status()
    return response.content


def email_certificate(job: dict, pdf_bytes: bytes) -> None:
    response = httpx.post(
        EMAIL_SERVICE_URL,
        json={
            "to": job["student_email"],
            "subject": f"Certificate: {job['course_title']}",
            "body": f"Congratulations {job['student_name']} on completing {job['course_title']}.",
        },
        files={"attachment": ("certificate.pdf", pdf_bytes, "application/pdf")},
    )
    response.raise_for_status()


def process_job(job: dict) -> None:
    pdf = generate_certificate_pdf(job)
    email_certificate(job, pdf)


def worker_loop(worker_id: int) -> None:
    while True:
        job = job_queue.get()
        try:
            process_job(job)
        except Exception as exc:
            print(f"worker {worker_id} failed: {exc}")
        finally:
            job_queue.task_done()


def start_worker_pool(size: int = WORKER_COUNT) -> None:
    for i in range(size):
        thread = threading.Thread(target=worker_loop, args=(i,), daemon=True)
        thread.start()


@app.on_event("startup")
def on_startup():
    start_worker_pool()


@app.post("/complete")
def complete_course(payload: CompletionRequest):
    job_queue.put(payload.model_dump())
    return {"queued": True, "queue_size": job_queue.qsize()}


@app.get("/queue/status")
def queue_status():
    return {"pending": job_queue.qsize(), "workers": WORKER_COUNT}
