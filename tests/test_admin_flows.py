import pytest
import uuid
from sqlalchemy import select
from app.models import User
from app.auth import create_access_token
from app.database import seed_default_admin

@pytest.mark.asyncio
async def test_admin_seeding(db_session):
    # Verify that seed_default_admin creates the admin
    # Let's delete the admin first if it exists in the test session (although database should be clean)
    from app.models import User, SemanticMemory
    res = await db_session.execute(select(User).where(User.email == "admin@navgurukul.org"))
    admin = res.scalar_one_or_none()
    if admin:
        await db_session.delete(admin)
        await db_session.commit()
    
    # Run seed function
    # Note: we need to temporarily set the session_maker to return our test transaction session
    # or override db.session_maker.
    from app.database import db
    old_maker = db.session_maker
    
    class FakeSessionMaker:
        def __init__(self, session):
            self.session = session
        def __call__(self):
            return self.session
    
    db.session_maker = FakeSessionMaker(db_session)
    try:
        await seed_default_admin()
    finally:
        db.session_maker = old_maker
        
    # Check that it exists now
    res = await db_session.execute(select(User).where(User.email == "admin@navgurukul.org"))
    admin = res.scalar_one_or_none()
    assert admin is not None
    assert admin.role == "admin"
    assert admin.status == "active"

@pytest.mark.asyncio
async def test_admin_login_success(client, db_session):
    # Register/ensure admin user exists
    from app.auth import hash_password
    res = await db_session.execute(select(User).where(User.email == "admin@navgurukul.org"))
    admin = res.scalar_one_or_none()
    if not admin:
        admin = User(
            email="admin@navgurukul.org",
            hashed_password=hash_password("navgurukul"),
            role="admin",
            status="active"
        )
        db_session.add(admin)
        await db_session.commit()
        
    response = await client.post("/v1/auth/login", json={
        "email": "admin@navgurukul.org",
        "password": "navgurukul"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_unauthorized_access_to_admin_endpoints(client, db_session):
    # Try accessing admin endpoints without a token
    resp1 = await client.get("/v1/admin/stats")
    assert resp1.status_code == 401
    
    # Register a student user and get token
    student_email = f"student_{uuid.uuid4()}@navgurukul.org"
    await client.post("/v1/auth/register", json={
        "email": student_email,
        "password": "student_pass",
        "role": "student"
    })
    
    login_resp = await client.post("/v1/auth/login", json={
        "email": student_email,
        "password": "student_pass"
    })
    assert login_resp.status_code == 200
    student_token = login_resp.json()["access_token"]
    
    # Try accessing admin endpoints with student token
    resp2 = await client.get("/v1/admin/stats", headers={"Authorization": f"Bearer {student_token}"})
    assert resp2.status_code == 403
    assert "Admin role required" in resp2.json()["detail"]

@pytest.mark.asyncio
async def test_admin_dashboard_operations(client, db_session):
    # Seed admin user
    from app.auth import hash_password
    admin = User(
        email=f"admin_{uuid.uuid4()}@navgurukul.org",
        hashed_password=hash_password("adminpass"),
        role="admin",
        status="active"
    )
    db_session.add(admin)
    
    # Seed students and mentors
    student = User(
        email=f"student_{uuid.uuid4()}@navgurukul.org",
        hashed_password=hash_password("password"),
        role="student",
        status="active"
    )
    db_session.add(student)
    
    mentor_pending = User(
        email=f"mentor_pending_{uuid.uuid4()}@navgurukul.org",
        hashed_password=hash_password("password"),
        role="mentor",
        status="pending"
    )
    db_session.add(mentor_pending)
    
    mentor_active = User(
        email=f"mentor_active_{uuid.uuid4()}@navgurukul.org",
        hashed_password=hash_password("password"),
        role="mentor",
        status="active"
    )
    db_session.add(mentor_active)
    
    await db_session.commit()
    
    admin_token = create_access_token(admin.id)
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test view all students
    resp = await client.get("/v1/admin/students", headers=headers)
    assert resp.status_code == 200
    students_list = resp.json()
    assert len(students_list) >= 1
    assert any(s["email"] == student.email for s in students_list)
    
    # Test search student by email
    resp = await client.get(f"/v1/admin/students?search={student.email}", headers=headers)
    assert resp.status_code == 200
    searched_students = resp.json()
    assert len(searched_students) == 1
    assert searched_students[0]["email"] == student.email
    
    # Test view all mentors
    resp = await client.get("/v1/admin/mentors", headers=headers)
    assert resp.status_code == 200
    mentors_list = resp.json()
    assert len(mentors_list) >= 2
    
    # Test filter mentors by status (pending)
    resp = await client.get("/v1/admin/mentors?status=pending", headers=headers)
    assert resp.status_code == 200
    pending_mentors = resp.json()
    assert any(m["email"] == mentor_pending.email for m in pending_mentors)
    assert not any(m["email"] == mentor_active.email for m in pending_mentors)
    
    # Test approve mentor request
    approve_resp = await client.post(f"/v1/admin/mentors/{mentor_pending.id}/approve", headers=headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "active"
    
    # Test deactivate mentor
    deactivate_resp = await client.post(f"/v1/admin/mentors/{mentor_active.id}/deactivate", headers=headers)
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["status"] == "suspended"
    
    # Test reject mentor
    reject_resp = await client.post(f"/v1/admin/mentors/{mentor_active.id}/reject", headers=headers)
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
    
    # Test activate mentor
    activate_resp = await client.post(f"/v1/admin/mentors/{mentor_active.id}/activate", headers=headers)
    assert activate_resp.status_code == 200
    assert activate_resp.json()["status"] == "active"
    
    # Test stats
    stats_resp = await client.get("/v1/admin/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_students" in stats
    assert "total_mentors" in stats
    assert "active_users" in stats
    assert "total_sessions" in stats
    assert "ai_usage" in stats
