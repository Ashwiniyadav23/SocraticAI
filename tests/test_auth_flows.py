import pytest
import uuid
from jose import jwt
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app.config import settings
from app.models import User
from sqlalchemy import select
from app.database import get_db

@pytest.mark.asyncio
async def test_email_registration(client, db_session):
    email = f"test_{uuid.uuid4()}@university.edu"
    response = await client.post("/v1/auth/register", json={
        "email": email,
        "password": "strongpassword123",
        "role": "student"
    })
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert data["email"] == email

@pytest.mark.asyncio
async def test_duplicate_email_registration(client, db_session):
    email = f"duplicate_{uuid.uuid4()}@university.edu"
    # First registration
    await client.post("/v1/auth/register", json={"email": email, "password": "pass", "role": "student"})
    # Second registration
    response = await client.post("/v1/auth/register", json={"email": email, "password": "pass", "role": "student"})
    assert response.status_code == 400
    assert "Email already registered" in response.text

@pytest.mark.asyncio
async def test_email_login(client, db_session):
    email = f"login_{uuid.uuid4()}@university.edu"
    await client.post("/v1/auth/register", json={"email": email, "password": "pass", "role": "student"})
    
    response = await client.post("/v1/auth/login", json={"email": email, "password": "pass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_google_signup_and_login(client, db_session, monkeypatch):
    import app.routers.auth_router
    email = f"google_{uuid.uuid4()}@gmail.com"
    
    # Mock requests.get to return a valid profile
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self): return self.json_data
        
    def mock_get(url, *args, **kwargs):
        if url == "https://www.googleapis.com/oauth2/v3/userinfo":
            return MockResponse({"email": email}, 200)
        return MockResponse({}, 404)
        
    monkeypatch.setattr(app.routers.auth_router.http_requests, "get", mock_get)
    
    # 3. Google Sign Up (First time login creates account)
    response = await client.post("/v1/auth/google", json={"token": "valid_fake_token"})
    assert response.status_code == 200
    token1 = response.json()["access_token"]
    
    # Verify user was created in DB
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.hashed_password is None
    
    # 4. Google Login (Second time uses existing account)
    response2 = await client.post("/v1/auth/google", json={"token": "valid_fake_token"})
    assert response2.status_code == 200
    token2 = response2.json()["access_token"]
    assert token2 is not None
    
@pytest.mark.asyncio
async def test_invalid_google_token(client, monkeypatch):
    import app.routers.auth_router
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code
    def mock_get(*args, **kwargs):
        return MockResponse(401)
    monkeypatch.setattr(app.routers.auth_router.http_requests, "get", mock_get)
    
    response = await client.post("/v1/auth/google", json={"token": "invalid_token"})
    assert response.status_code == 401
    assert "Invalid Google token" in response.text

@pytest.mark.asyncio
async def test_jwt_validation_and_protected_route(client, db_session):
    # Register and login to get JWT
    email = f"protected_{uuid.uuid4()}@university.edu"
    await client.post("/v1/auth/register", json={"email": email, "password": "pass", "role": "student"})
    login_resp = await client.post("/v1/auth/login", json={"email": email, "password": "pass"})
    token = login_resp.json()["access_token"]
    
    # 9. Protected Route Access (assuming /v1/session requires auth)
    response = await client.post("/v1/session", json={"concept_name": "Test Concept"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [200, 201] # Depends on exact implementation, but should not be 401

@pytest.mark.asyncio
async def test_invalid_jwt_handling(client):
    response = await client.post("/v1/session", json={"concept_name": "Test"}, headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_expired_jwt_handling(client, db_session):
    email = f"expired_{uuid.uuid4()}@university.edu"
    await client.post("/v1/auth/register", json={"email": email, "password": "pass", "role": "student"})
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    # Create expired token
    expire = datetime.now(timezone.utc) - timedelta(minutes=15)
    to_encode = {"sub": str(user.id), "exp": expire}
    expired_token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    response = await client.post("/v1/session", json={"concept_name": "Test"}, headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
