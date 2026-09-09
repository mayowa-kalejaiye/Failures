"""Tests for course access control and admin-gated course creation."""


async def test_list_courses_is_public(client, course):
    resp = await client.get("/courses")
    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.json()]
    assert "test-course" in slugs


async def test_get_course_detail_hides_content(client, course):
    resp = await client.get(f"/courses/{course.id}")
    assert resp.status_code == 200
    # The public detail schema must not leak the protected material.
    assert "content" not in resp.json()


async def test_content_requires_enrollment(client, course, make_auth_headers):
    headers = await make_auth_headers()
    resp = await client.get(f"/courses/{course.id}/content", headers=headers)
    assert resp.status_code == 403


async def test_content_missing_course_404(client, make_auth_headers):
    headers = await make_auth_headers()
    resp = await client.get("/courses/99999/content", headers=headers)
    assert resp.status_code == 404


async def test_create_course_requires_admin(client, make_auth_headers):
    payload = {
        "title": "New Course",
        "slug": "new-course",
        "price": "9999.00",
        "content": "secret",
    }
    # Unauthenticated.
    assert (await client.post("/courses", json=payload)).status_code == 401
    # Authenticated but not an admin.
    headers = await make_auth_headers()
    assert (await client.post("/courses", json=payload, headers=headers)).status_code == 403


async def test_admin_can_create_course(client, make_admin_headers):
    headers = await make_admin_headers()
    payload = {
        "title": "Admin Course",
        "slug": "admin-course",
        "price": "9999.00",
        "content": "secret",
    }
    resp = await client.post("/courses", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "admin-course"
