import uuid
from app.models import User
from app.auth import hash_password

async def test_authentication_flow(client, db_session):
    pwd = "testpassword123"
    user_id = uuid.uuid4()
    user = User(id=user_id, email="auth@example.com", hashed_password=hash_password(pwd))
    db_session.add(user)
    await db_session.commit()
    
    response = await client.post("/v1/auth/login", json={"email": "auth@example.com", "password": pwd})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

async def test_authorization_rbac(client, db_session):
    response = await client.post("/v1/session", json={"concept_name": "Test Concept"})
    assert response.status_code == 401
