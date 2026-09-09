async def test_register_and_login(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "a@test.com", "password": "password123", "full_name": "A"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "a@test.com"
    assert "password" not in body and "hashed_password" not in body

    resp = await client.post(
        "/auth/login", data={"username": "a@test.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"]


async def test_duplicate_registration_conflicts(client):
    payload = {"email": "dup@test.com", "password": "password123"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    assert (await client.post("/auth/register", json=payload)).status_code == 409


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register", json={"email": "b@test.com", "password": "password123"}
    )
    resp = await client.post(
        "/auth/login", data={"username": "b@test.com", "password": "wrongpassword"}
    )
    assert resp.status_code == 401


async def test_protected_route_requires_token(client):
    resp = await client.get("/me/enrollments")
    assert resp.status_code == 401
