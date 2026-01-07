import pytest
import os
import tempfile
import shutil
from unittest.mock import patch

# Assuming 'app' is the package name where create_app, db, bcrypt, and User model reside.
# Adjust imports based on your actual project structure.
# For example, if create_app is in myapp/__init__.py, and db, bcrypt are also there,
# and User model is in myapp/models.py, then:
from app import create_app, db, bcrypt
from app.models import User

@pytest.fixture(scope='function')
def app():
    """
    Fixture for the Flask application instance.

    Sets up a test Flask application with an in-memory SQLite database
    and a temporary directory for QR code storage. The application context
    is pushed for the duration of the tests, and resources are cleaned up
    after each test function.
    """
    # Create a temporary directory for QR code storage during tests
    temp_qr_storage_dir = tempfile.mkdtemp()

    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'super-secret-test-key-for-qr-genius',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for easier testing
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,  # Recommended for SQLAlchemy
        'QR_CODE_STORAGE_PATH': temp_qr_storage_dir,  # Use temporary storage
        'QR_CODE_BASE_URL': 'http://testserver/downloads/', # Base URL for generated QR download links
        'MAIL_SUPPRESS_SEND': True, # Suppress email sending during tests
        'SERVER_NAME': 'localhost.localdomain:5000' # Required for url_for in some contexts
    }
    
    # Create the Flask app with test configurations
    # Assuming create_app function can accept a dictionary of test configurations
    # or has a mechanism to load them.
    # Example: create_app(config_class=TestConfig) or create_app(test_config=test_config)
    # Adjust this call based on your actual create_app signature.
    # For this example, we assume create_app accepts a 'test_config' dict.
    flask_app = create_app(test_config=test_config)

    # Push an application context to make 'current_app' and database operations available
    with flask_app.app_context():
        yield flask_app

    # Clean up the temporary directory after the test function finishes
    shutil.rmtree(temp_qr_storage_dir)

@pytest.fixture(scope='function')
def database(app):
    """
    Fixture for setting up and tearing down the database for each test function.

    It creates all database tables before a test runs and drops them afterwards,
    ensuring a clean state for every test. This fixture depends on the 'app' fixture
    to get the configured Flask application context.
    """
    with app.app_context():
        db.create_all()  # Create all tables defined in models
        yield db  # Provide the db object to tests
        db.session.remove()  # Ensure the session is closed
        db.drop_all()  # Drop all tables to clean up

@pytest.fixture(scope='function')
def client(app, database):
    """
    Fixture for the Flask test client.

    Provides a client to make requests to the Flask application during tests.
    It depends on the 'app' and 'database' fixtures to ensure the app is configured
    and the database is set up before requests are made.
    """
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """
    Fixture for the Flask CLI test runner.

    Provides a runner to invoke Flask CLI commands during tests.
    It depends on the 'app' fixture.
    """
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def test_user(app, database):
    """
    Fixture to create and return a test user for authentication purposes.

    A test user is created in the database with a hashed password. This user
    can then be used by other fixtures (e.g., `auth_client`) or directly
    in tests. The user is cleaned up implicitly by the `database` fixture's
    `db.drop_all()` call.
    """
    with app.app_context():
        # Hash a sample password using bcrypt
        hashed_password = bcrypt.generate_password_hash("password123").decode('utf-8')
        user = User(email="test@example.com", hashed_password=hashed_password)
        db.session.add(user)
        db.session.commit()
        yield user

@pytest.fixture(scope='function')
def auth_client(client, test_user):
    """
    Fixture for an authenticated Flask test client.

    Logs in the `test_user` using the application's login API endpoint
    and returns a client that maintains the authenticated session. This allows
    testing endpoints that require user authentication.
    """
    login_data = {
        'email': test_user.email,
        'password': 'password123'
    }
    # Make a POST request to the login endpoint
    response = client.post('/api/login', json=login_data)

    # Assert that the login was successful
    assert response.status_code == 200
    assert response.json is not None
    assert response.json.get('message') == 'Login successful'

    # The client object now holds the session cookie from the successful login
    return client

@pytest.fixture(scope='function')
def mock_qr_code_generation():
    """
    Fixture to mock the QR code generation library.

    This prevents actual QR code image generation during tests, making them
    faster and preventing filesystem writes. It patches the 'qrcode' library's
    make method to return a dummy object.
    """
    with patch('qrcode.make') as mock_make:
        # Configure the mock to return a dummy object that has a save method
        mock_qr_image = type('MockQRImage', (object,), {'save': lambda self, path: None})()
        mock_make.return_value = mock_qr_image
        yield mock_make