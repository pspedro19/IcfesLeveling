"""
Authentication endpoint tests for the ICFES Leveling backend.

Routes under test:
  POST /api/v1/auth/register
  POST /api/v1/auth/login       (OAuth2 form-data)
  GET  /api/v1/auth/me
  POST /api/v1/auth/refresh
  POST /api/v1/auth/logout
"""
import pytest
import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    verify_token,
)
from tests.conftest import auth_header_for, create_test_user_record


# Strong password that passes UserCreate validation:
#   min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
STRONG_PASSWORD = "SecurePass123#"


# ============================================================================
# TestAuthEndpoints — Register / Login / Refresh / Logout / Me
# ============================================================================

class TestAuthEndpoints:
    """Test authentication endpoints."""

    # ----- Register -----

    def test_register_user_success(self, client: TestClient, db: Session):
        """POST /api/v1/auth/register creates a user and returns UserResponse."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": STRONG_PASSWORD,
            "display_name": "New User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200, f"Register failed: {response.text}"

        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        # password hash should never appear in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Verify user exists in database
        user = db.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_register_user_duplicate_username(self, client: TestClient, db: Session):
        """Duplicate username returns 400."""
        create_test_user_record(db, username="dupeuser", email="orig@example.com")
        user_data = {
            "username": "dupeuser",
            "email": "different@example.com",
            "password": STRONG_PASSWORD,
            "display_name": "Different User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400

    def test_register_user_duplicate_email(self, client: TestClient, db: Session):
        """Duplicate email returns 400."""
        create_test_user_record(db, username="origuser", email="dupe@example.com")
        user_data = {
            "username": "differentuser",
            "email": "dupe@example.com",
            "password": STRONG_PASSWORD,
            "display_name": "Different User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400

    def test_register_user_invalid_email(self, client: TestClient):
        """Invalid email format returns 422."""
        user_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": STRONG_PASSWORD,
            "display_name": "New User",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_user_weak_password(self, client: TestClient):
        """Weak password (missing requirements) returns 422."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",  # Too short, missing requirements
            "display_name": "New User",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    # ----- Login (uses OAuth2PasswordRequestForm → form data) -----

    def test_login_success(self, client: TestClient, db: Session):
        """POST /api/v1/auth/login with valid credentials returns tokens."""
        # Create user with known password
        hashed = get_password_hash(STRONG_PASSWORD)
        user = create_test_user_record(
            db, username="loginuser", email="login@example.com",
            hashed_password=hashed,
        )

        # OAuth2PasswordRequestForm expects form-encoded data
        response = client.post("/api/v1/auth/login", data={
            "username": "loginuser",
            "password": STRONG_PASSWORD,
        })
        assert response.status_code == 200, f"Login failed: {response.text}"

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid_username(self, client: TestClient):
        """Login with non-existent user returns 401."""
        response = client.post("/api/v1/auth/login", data={
            "username": "nonexistent",
            "password": "anypassword",
        })
        assert response.status_code == 401

    def test_login_wrong_password(self, client: TestClient, db: Session):
        """Login with wrong password returns 401."""
        hashed = get_password_hash(STRONG_PASSWORD)
        create_test_user_record(
            db, username="wrongpwuser", email="wrongpw@example.com",
            hashed_password=hashed,
        )
        response = client.post("/api/v1/auth/login", data={
            "username": "wrongpwuser",
            "password": "WrongPassword123#",
        })
        assert response.status_code == 401

    # ----- Refresh Token -----

    def test_refresh_token_success(self, client: TestClient, db: Session):
        """POST /api/v1/auth/refresh with valid refresh token returns new tokens."""
        from app.models.refresh_token import RefreshToken as RefreshTokenModel
        from datetime import datetime

        user = create_test_user_record(db)
        refresh_str, refresh_payload = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=7),
            return_payload=True,
        )

        # Store refresh token in DB
        db_token = RefreshTokenModel(
            user_id=user.id,
            jti=refresh_payload["jti"],
            expires_at=datetime.fromtimestamp(refresh_payload["exp"]),
        )
        db.add(db_token)
        db.commit()

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_str,
        })
        assert response.status_code == 200, f"Refresh failed: {response.text}"

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """POST /api/v1/auth/refresh with invalid token returns 401."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "not-a-valid-jwt",
        })
        assert response.status_code == 401

    def test_refresh_token_missing_body(self, client: TestClient):
        """POST /api/v1/auth/refresh without body returns 422."""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 422

    # ----- Get Current User (/me) -----

    def test_get_current_user_success(self, client: TestClient, db: Session):
        """GET /api/v1/auth/me with valid token returns user info."""
        user = create_test_user_record(db, username="meuser")
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_header_for(user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"

    def test_get_current_user_no_token(self, client: TestClient):
        """GET /api/v1/auth/me without token returns 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """GET /api/v1/auth/me with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert response.status_code == 401

    # ----- Logout -----

    def test_logout_success(self, client: TestClient, db: Session):
        """POST /api/v1/auth/logout revokes refresh token."""
        from app.models.refresh_token import RefreshToken as RefreshTokenModel
        from datetime import datetime

        user = create_test_user_record(db)
        refresh_str, refresh_payload = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=7),
            return_payload=True,
        )

        db_token = RefreshTokenModel(
            user_id=user.id,
            jti=refresh_payload["jti"],
            expires_at=datetime.fromtimestamp(refresh_payload["exp"]),
        )
        db.add(db_token)
        db.commit()

        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_str},
            headers=auth_header_for(user.id),
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


# ============================================================================
# TestPasswordSecurity — hash / verify
# ============================================================================

class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_get_password_hash(self):
        hashed = get_password_hash("testpassword123")
        assert hashed != "testpassword123"
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        hashed = get_password_hash("testpassword123")
        assert verify_password("testpassword123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = get_password_hash("testpassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        hashed = get_password_hash("testpassword123")
        assert verify_password("", hashed) is False


# ============================================================================
# TestJWTTokens — create / verify tokens
# ============================================================================

class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        token = create_access_token(data={"sub": "test-user-123"})
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_create_access_token_with_expire(self):
        token = create_access_token(
            data={"sub": "test-user-123"},
            expires_delta=timedelta(hours=1),
        )
        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_valid_token(self):
        token = create_access_token(data={"sub": "test-user-123"})
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-123"
        assert payload["type"] == "access"

    def test_verify_invalid_token_returns_none(self):
        """verify_token returns None for invalid tokens."""
        result = verify_token("invalid-token-string")
        assert result is None

    def test_verify_tampered_token_returns_none(self):
        """Tampered JWT should return None."""
        token = create_access_token(data={"sub": "test-user-123"})
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        result = verify_token(tampered)
        assert result is None


# ============================================================================
# TestAuthMiddleware — protected endpoint behavior
# ============================================================================

class TestAuthMiddleware:
    """Test that protected endpoints require valid auth."""

    def test_protected_endpoint_with_valid_token(self, client: TestClient, db: Session):
        """Valid token allows access to /auth/me."""
        user = create_test_user_record(db)
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_header_for(user.id),
        )
        assert response.status_code == 200

    def test_protected_endpoint_without_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_malformed_token(self, client: TestClient):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat token"},
        )
        assert response.status_code == 401

    def test_protected_endpoint_with_empty_token(self, client: TestClient):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401


# ============================================================================
# TestAuthIntegration — full flows
# ============================================================================

class TestAuthIntegration:
    """Integration tests for authentication flow."""

    def test_full_registration_login_flow(self, client: TestClient, db: Session):
        """Register → Login → Access /me."""
        # 1. Register
        user_data = {
            "username": "flowuser",
            "email": "flow@example.com",
            "password": STRONG_PASSWORD,
            "display_name": "Flow User",
        }
        reg_response = client.post("/api/v1/auth/register", json=user_data)
        assert reg_response.status_code == 200

        # 2. Login (form data)
        login_response = client.post("/api/v1/auth/login", data={
            "username": "flowuser",
            "password": STRONG_PASSWORD,
        })
        assert login_response.status_code == 200

        login_data = login_response.json()
        assert "access_token" in login_data

        # 3. Access protected route with the token
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_data['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowuser"

    def test_token_refresh_flow(self, client: TestClient, db: Session):
        """Login → Refresh → Use new token."""
        hashed = get_password_hash(STRONG_PASSWORD)
        create_test_user_record(
            db, username="refreshuser", email="refresh@example.com",
            hashed_password=hashed,
        )

        # Login
        login_response = client.post("/api/v1/auth/login", data={
            "username": "refreshuser",
            "password": STRONG_PASSWORD,
        })
        assert login_response.status_code == 200
        login_data = login_response.json()

        # Refresh
        refresh_response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": login_data["refresh_token"],
        })
        assert refresh_response.status_code == 200, f"Refresh failed: {refresh_response.text}"
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens

        # Use new token
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert me_response.status_code == 200

    def test_concurrent_login_attempts(self, client: TestClient, db: Session):
        """Multiple login attempts should all succeed."""
        hashed = get_password_hash(STRONG_PASSWORD)
        create_test_user_record(
            db, username="concuser", email="conc@example.com",
            hashed_password=hashed,
        )

        responses = []
        for _ in range(3):
            r = client.post("/api/v1/auth/login", data={
                "username": "concuser",
                "password": STRONG_PASSWORD,
            })
            responses.append(r)

        for r in responses:
            assert r.status_code == 200
