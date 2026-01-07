import pytest
import json
import tempfile
import os
from unittest.mock import patch

from app import create_app, db
from app.models import User

# --- Fixtures ---

@pytest.fixture(scope='module')
def test_app():
    """
    Fixture to set up a Flask application for testing.
    Uses an in-memory SQLite database for isolation and speed.
    """
    # Create a temporary SQLite database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create the Flask app instance
    app = create_app()

    # Configure the app for testing
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for easier testing
        "LOGIN_DISABLED": False,  # Ensure Flask-Login is active
        "SECRET_KEY": "test_secret_key_for_integration", # Required for session management
    })

    # Establish an application context
    with app.app_context():
        # Initialize the database with the app
        db.init_app(app)
        # Create all database tables
        db.create_all()

    yield app

    # Teardown: close and remove the temporary database file
    with app.app_context():
        db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def client(test_app):
    """
    Fixture to provide a test client for making requests to the Flask app.
    Ensures a clean database state for each test function.
    """
    with test_app.test_client() as client:
        # Push an application context for the test
        with test_app.app_context():
            # Clean up the database before each test
            db.session.remove()
            db.drop_all()
            db.create_all()
        yield client
        # Clean up after each test (optional, as db.drop_all() is called before each test)
        with test_app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

# --- Helper Functions for Tests ---

def register_user(client, email, password):
    """
    Helper function to register a user via the API.
    """
    return client.post(
        '/api/register',
        data=json.dumps({'email': email, 'password': password}),
        content_type='application/json'
    )

def login_user(client, email, password):
    """
    Helper function to log in a user via the API.
    """
    return client.post(
        '/api/login',
        data=json.dumps({'email': email, 'password': password}),
        content_type='application/json'
    )

def logout_user(client):
    """
    Helper function to log out a user via the API.
    """
    return client.post('/api/logout')

# --- Integration Tests for Authentication Routes ---

class TestAuthRoutes:
    """
    Integration tests for authentication-related API endpoints.
    """

    def test_register_success(self, client):
        """
        Test successful user registration.
        """
        email = "test@example.com"
        password = "SecurePassword123!"
        
        response = register_user(client, email, password)
        data = json.loads(response.data)

        assert response.status_code == 201
        assert "message" in data
        assert "User registered successfully." in data["message"]
        assert "user_id" in data

        # Verify user exists in the database
        with client.application.app_context():
            user = User.query.filter_by(email=email).first()
            assert user is not None
            assert user.email == email
            assert user.check_password(password)

    def test_register_existing_email(self, client):
        """
        Test registration with an email that already exists.
        """
        email = "existing@example.com"
        password = "SecurePassword123!"

        # Register the user first
        register_user(client, email, password)

        # Try to register again with the same email
        response = register_user(client, email, password)
        data = json.loads(response.data)

        assert response.status_code == 409  # Conflict
        assert "message" in data
        assert "Email already registered." in data["message"]

    def test_register_missing_fields(self, client):
        """
        Test registration with missing required fields (e.g., email or password).
        """
        # Missing email
        response = client.post(
            '/api/register',
            data=json.dumps({'password': 'password'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert response.status_code == 400
        assert "message" in data
        assert "Email and password are required." in data["message"]

        # Missing password
        response = client.post(
            '/api/register',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert response.status_code == 400
        assert "message" in data
        assert "Email and password are required." in data["message"]
        
        # Missing both
        response = client.post(
            '/api/register',
            data=json.dumps({}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert response.status_code == 400
        assert "message" in data
        assert "Email and password are required." in data["message"]

    def test_register_invalid_email_format(self, client):
        """
        Test registration with an invalid email format.
        """
        response = register_user(client, "invalid-email", "password123")
        data = json.loads(response.data)

        assert response.status_code == 400
        assert "message" in data
        assert "Invalid email format." in data["message"]

    def test_login_success(self, client):
        """
        Test successful user login.
        """
        email = "login_test@example.com"
        password = "LoginSecurePassword123!"

        # Register the user first
        register_user(client, email, password)

        # Attempt to log in
        response = login_user(client, email, password)
        data = json.loads(response.data)

        assert response.status_code == 200
        assert "message" in data
        assert "Logged in successfully." in data["message"]
        assert "user_id" in data
        # Flask-Login sets a session cookie. We can't directly check `current_user.is_authenticated`
        # in the test client's response, but the success message and status code are good indicators.
        # The presence of a `Set-Cookie` header for the session is another good indicator.
        assert 'Set-Cookie' in response.headers
        assert 'session=' in response.headers['Set-Cookie']

    def test_login_invalid_credentials(self, client):
        """
        Test login with incorrect password for an existing user.
        """
        email = "wrongpass@example.com"
        password = "CorrectPassword123!"

        # Register the user
        register_user(client, email, password)

        # Attempt to log in with wrong password
        response = login_user(client, email, "WrongPassword!")
        data = json.loads(response.data)

        assert response.status_code == 401  # Unauthorized
        assert "message" in data
        assert "Invalid email or password." in data["message"]

    def test_login_non_existent_user(self, client):
        """
        Test login with an email that is not registered.
        """
        response = login_user(client, "nonexistent@example.com", "AnyPassword123!")
        data = json.loads(response.data)

        assert response.status_code == 401  # Unauthorized
        assert "message" in data
        assert "Invalid email or password." in data["message"]

    def test_login_missing_fields(self, client):
        """
        Test login with missing required fields (email or password).
        """
        # Missing email
        response = client.post(
            '/api/login',
            data=json.dumps({'password': 'password'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert response.status_code == 400
        assert "message" in data
        assert "Email and password are required." in data["message"]

        # Missing password
        response = client.post(
            '/api/login',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert response.status_code == 400
        assert "message" in data
        assert "Email and password are required." in data["message"]
        
        # Missing both
        response = client.post(
            '/api/login',
            data=json.dumps({}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert response.status_code == 400
        assert "message" in data
        assert "Email and password are required." in data["message"]

    def test_logout_success(self, client):
        """
        Test successful user logout after being logged in.
        """
        email = "logout_user@example.com"
        password = "LogoutSecurePassword123!"

        # Register and log in the user
        register_user(client, email, password)
        login_response = login_user(client, email, password)
        assert login_response.status_code == 200

        # Attempt to log out
        response = logout_user(client)
        data = json.loads(response.data)

        assert response.status_code == 200
        assert "message" in data
        assert "Logged out successfully." in data["message"]
        
        # Verify session cookie is cleared (or at least not present for authentication)
        # The test client doesn't explicitly show session invalidation, but a successful 200
        # and message from the server is the primary indicator for an API logout.
        # A subsequent request to a protected endpoint would confirm actual logout.

    def test_logout_not_logged_in(self, client):
        """
        Test logout when no user is currently logged in.
        Flask-Login's `logout_user` handles this gracefully, so it should still return 200.
        """
        response = logout_user(client)
        data = json.loads(response.data)

        assert response.status_code == 200
        assert "message" in data
        assert "Logged out successfully." in data["message"] # Or similar message indicating no active session.
                                                          # Flask-Login's logout_user doesn't error if not logged in.