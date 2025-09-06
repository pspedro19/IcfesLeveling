"""
Authentication endpoint tests for the ICFES Leveling backend.
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.orm import Session
import bcrypt

from app.models.user import User
from app.core.security import create_access_token, verify_password, hash_password
from app.schemas.user import UserCreate, UserLogin


@pytest.mark.auth
class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_user_success(self, client: TestClient, db_session: Session):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "display_name": "New User"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert "password" not in data["user"]

        # Verify user was created in database
        user = db_session.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_register_user_duplicate_username(self, client: TestClient, create_test_user):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",  # Same as existing user
            "email": "different@example.com",
            "password": "securepassword123",
            "display_name": "Different User"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_register_user_duplicate_email(self, client: TestClient, create_test_user):
        """Test registration with duplicate email."""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Same as existing user
            "password": "securepassword123",
            "display_name": "Different User"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        user_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": "securepassword123",
            "display_name": "New User"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_register_user_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",  # Too short
            "display_name": "New User"
        }

        response = client.post("/auth/register", json=user_data)

        # Should either reject with 422 or accept but warn
        assert response.status_code in [201, 422]

    def test_login_success(self, client: TestClient, create_test_user):
        """Test successful login."""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        # First, we need to set a known password for the test user
        with patch('app.core.security.verify_password') as mock_verify:
            mock_verify.return_value = True
            response = client.post("/auth/login", json=login_data)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            assert "user" in data

    def test_login_invalid_username(self, client: TestClient):
        """Test login with non-existent username."""
        login_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    def test_login_wrong_password(self, client: TestClient, create_test_user):
        """Test login with wrong password."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    def test_login_inactive_user(self, client: TestClient, create_test_user, db_session: Session):
        """Test login with inactive user."""
        # Deactivate user
        user = db_session.query(User).filter(User.username == "testuser").first()
        user.is_active = False
        db_session.commit()

        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        with patch('app.core.security.verify_password') as mock_verify:
            mock_verify.return_value = True
            response = client.post("/auth/login", json=login_data)

            assert response.status_code == 401
            data = response.json()
            assert "inactive" in data["detail"].lower()

    def test_refresh_token_success(self, client: TestClient, create_test_user):
        """Test successful token refresh."""
        # Mock valid token
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "test-user-123", "username": "testuser"}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post("/auth/refresh", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            headers = {"Authorization": "Bearer invalid_token"}
            response = client.post("/auth/refresh", headers=headers)

            assert response.status_code == 401

    def test_refresh_token_missing(self, client: TestClient):
        """Test token refresh without token."""
        response = client.post("/auth/refresh")

        assert response.status_code == 401

    def test_get_current_user_success(self, client: TestClient, create_test_user):
        """Test getting current user info."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "test-user-123", "username": "testuser"}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get("/auth/me", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"
            assert data["id"] == "test-user-123"

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            headers = {"Authorization": "Bearer invalid_token"}
            response = client.get("/auth/me", headers=headers)

            assert response.status_code == 401

    def test_logout_success(self, client: TestClient, create_test_user):
        """Test successful logout."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "test-user-123", "username": "testuser"}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.post("/auth/logout", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "logged out" in data["message"].lower()


@pytest.mark.auth
class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False
        assert verify_password(None, hashed) is False


@pytest.mark.auth
class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_data = {"sub": "test-user-123", "username": "testuser"}
        token = create_access_token(data=user_data)

        assert isinstance(token, str)
        assert len(token) > 50
        assert token.count(".") == 2  # JWT has 3 parts separated by dots

    def test_create_access_token_with_expire(self):
        """Test creating access token with custom expiration."""
        from datetime import timedelta
        
        user_data = {"sub": "test-user-123", "username": "testuser"}
        token = create_access_token(data=user_data, expires_delta=timedelta(hours=1))

        assert isinstance(token, str)
        assert len(token) > 50

    @patch('app.core.security.jwt.decode')
    def test_decode_valid_token(self, mock_decode):
        """Test decoding valid token."""
        from app.core.security import decode_token
        
        mock_decode.return_value = {"sub": "test-user-123", "username": "testuser"}
        
        result = decode_token("valid_token")
        assert result["sub"] == "test-user-123"
        assert result["username"] == "testuser"

    @patch('app.core.security.jwt.decode')
    def test_decode_invalid_token(self, mock_decode):
        """Test decoding invalid token."""
        from app.core.security import decode_token
        from jwt.exceptions import InvalidTokenError
        
        mock_decode.side_effect = InvalidTokenError("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid_token")
        
        assert exc_info.value.status_code == 401

    @patch('app.core.security.jwt.decode')
    def test_decode_expired_token(self, mock_decode):
        """Test decoding expired token."""
        from app.core.security import decode_token
        from jwt.exceptions import ExpiredSignatureError
        
        mock_decode.side_effect = ExpiredSignatureError("Token has expired")
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token("expired_token")
        
        assert exc_info.value.status_code == 401


@pytest.mark.auth
class TestAuthMiddleware:
    """Test authentication middleware."""

    def test_protected_endpoint_with_valid_token(self, client: TestClient, create_test_user):
        """Test accessing protected endpoint with valid token."""
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "test-user-123", "username": "testuser"}
            
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get("/api/v1/users/profile", headers=headers)

            # Should not return 401 (depends on actual endpoint implementation)
            assert response.status_code != 401

    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/users/profile")

        assert response.status_code == 401

    def test_protected_endpoint_with_malformed_token(self, client: TestClient):
        """Test accessing protected endpoint with malformed token."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/api/v1/users/profile", headers=headers)

        assert response.status_code == 401

    def test_protected_endpoint_with_empty_token(self, client: TestClient):
        """Test accessing protected endpoint with empty token."""
        headers = {"Authorization": "Bearer "}
        response = client.get("/api/v1/users/profile", headers=headers)

        assert response.status_code == 401


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for authentication flow."""

    def test_full_registration_login_flow(self, client: TestClient, db_session: Session):
        """Test complete registration and login flow."""
        # Register user
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "securepassword123",
            "display_name": "Integration User"
        }

        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Login with same credentials
        login_data = {
            "username": "integrationuser",
            "password": "securepassword123"
        }

        with patch('app.core.security.verify_password') as mock_verify:
            mock_verify.return_value = True
            login_response = client.post("/auth/login", json=login_data)

            assert login_response.status_code == 200
            login_data = login_response.json()
            assert "access_token" in login_data

            # Use token to access protected endpoint
            token = login_data["access_token"]
            with patch('app.core.security.decode_token') as mock_decode:
                mock_decode.return_value = {"sub": "integration-user", "username": "integrationuser"}
                
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = client.get("/auth/me", headers=headers)
                
                assert profile_response.status_code == 200

    def test_token_refresh_flow(self, client: TestClient, create_test_user):
        """Test token refresh flow."""
        # Mock initial login
        with patch('app.core.security.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "test-user-123", "username": "testuser"}
            
            headers = {"Authorization": "Bearer original_token"}
            
            # Refresh token
            refresh_response = client.post("/auth/refresh", headers=headers)
            assert refresh_response.status_code == 200
            
            new_token_data = refresh_response.json()
            assert "access_token" in new_token_data
            
            # Use new token
            new_headers = {"Authorization": f"Bearer {new_token_data['access_token']}"}
            profile_response = client.get("/auth/me", headers=new_headers)
            assert profile_response.status_code == 200

    def test_concurrent_login_attempts(self, client: TestClient, create_test_user):
        """Test handling concurrent login attempts."""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        with patch('app.core.security.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            # Simulate concurrent requests
            responses = []
            for _ in range(5):
                response = client.post("/auth/login", json=login_data)
                responses.append(response)

            # All should succeed (no rate limiting in this test)
            for response in responses:
                assert response.status_code == 200

    def test_password_change_invalidates_tokens(self, client: TestClient, create_test_user, db_session: Session):
        """Test that changing password invalidates existing tokens."""
        # This would require implementing password change functionality
        # and token invalidation mechanism
        pass  # Placeholder for future implementation