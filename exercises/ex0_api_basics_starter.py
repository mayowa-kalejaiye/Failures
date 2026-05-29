"""
Exercise 0 — API Basics (Starter)

Goal: Teach how to design and implement a small HTTP API from the ground up.

Work through the TODOs in order. Keep changes small and test each step.

Runs on port 8000 by default in the examples, but the file is self-contained.
"""

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Exercise 0: API Basics")


class CreateUserRequest(BaseModel):
    email: str = Field(..., description="User email")
    name: str = Field(..., description="Full name")


class UserResponse(BaseModel):
    id: int
    email: str
    name: str


# In-memory store for the exercise (no DB required)
_users = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: CreateUserRequest):
    """
    TODOs:
    1. Validate `email` looks like an email (use simple check or regex).
    2. Prevent duplicate emails (return 409 on duplicate).
    3. Add the user to `_users` and return the created user with an `id`.
    4. Add logging or print statements to observe flow.
    """
    # Simple duplicate check
    for u in _users:
        if u["email"] == payload.email:
            raise HTTPException(status_code=409, detail="Email already registered")

    user = {"id": len(_users) + 1, "email": payload.email, "name": payload.name}
    _users.append(user)
    return user


@app.get("/users", response_model=List[UserResponse])
def list_users(limit: int = Query(10, ge=1, le=100)):
    """
    TODOs:
    - Support `limit` query param to control results.
    - Consider adding pagination (optional).
    """
    return _users[:limit]


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int = Path(..., ge=1)):
    """
    TODOs:
    - Return 404 if the user does not exist.
    """
    for u in _users:
        if u["id"] == user_id:
            return u
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/debug/reset")
def reset_store():
    """Helper endpoint for local testing to reset the in-memory store."""
    _users.clear()
    return {"reset": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
