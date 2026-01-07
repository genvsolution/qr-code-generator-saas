import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, QRCode
from werkzeug.security import check_password_hash

# --- Fixtures ---

@pytest.fixture(scope='module')
def test_app():
    """
    Fixture to create a test Flask application context for the entire module.
    It sets up an in-memory SQLite database and tears it down after all tests
    in the module have completed.
    """
    # Assuming `create_app` can accept a string 'testing' to load a test configuration.
    # The TestConfig should configure an in-memory SQLite database.
    app = create_app('testing')
    with app.app_context():
        db.create_all()  # Create tables for all models
        yield app
        db.session.remove()
        db.drop_all()    # Drop tables after all tests in the module

@pytest.fixture(scope='function')
def session(test_app):
    """
    Fixture to provide a clean database session for each test function.
    It uses a transaction that is rolled back after each test, ensuring
    test isolation and a clean slate for subsequent tests.
    """
    with test_app.app_context():
        # Establish a connection and begin a transaction
        connection = db.engine.connect()
        transaction = connection.begin()

        # Bind the session to the connection for the duration of the test
        db.session.configure(bind=connection)

        yield db.session

        # Rollback the transaction to undo any changes made during the test
        transaction.rollback()
        # Close the connection
        connection.close()
        # Remove the session
        db.session.remove()

# --- Test Cases for User Model ---

class TestUserModel:
    """
    Unit tests for the User database model and its methods.
    """

    def test_create_user(self, session):
        """
        Test that a User object can be created and persisted correctly,
        including automatic password hashing and a default `created_at` timestamp.
        """
        email = "test@example.com"
        password = "securepassword123"
        user = User(email=email, password=password)
        session.add(user)
        session.commit()

        retrieved_user = User.query.filter_by(email=email).first()

        assert retrieved_user is not None
        assert retrieved_user.email == email
        # Verify password hashing using Bcrypt's check_password_hash
        assert check_password_hash(retrieved_user.password_hash, password)
        assert isinstance(retrieved_user.created_at, datetime)
        # Check that generated_at is recent (within 5 seconds of now)
        assert (datetime.utcnow() - retrieved_user.created_at).total_seconds() < 5

    def test_set_password(self, session):
        """
        Test the `set_password` method to ensure it correctly hashes and updates
        the user's password_hash attribute.
        """
        user = User(email="setpass@example.com")
        session.add(user)
        session.flush()  # Ensure user has an ID before committing if needed

        new_password = "new_secure_password"
        user.set_password(new_password)
        session.commit()

        retrieved_user = User.query.filter_by(email="setpass@example.com").first()
        assert retrieved_user is not None
        assert check_password_hash(retrieved_user.password_hash, new_password)
        # Ensure an incorrect password does not pass verification
        assert not check_password_hash(retrieved_user.password_hash, "wrong_password")

    def test_check_password(self, session):
        """
        Test the `check_password` method for accurate password verification
        against the stored hash.
        """
        email = "checkpass@example.com"
        password = "anotherpassword456"
        user = User(email=email, password=password)
        session.add(user)
        session.commit()

        retrieved_user = User.query.filter_by(email=email).first()
        assert retrieved_user is not None
        assert retrieved_user.check_password(password)
        assert not retrieved_user.check_password("wrongpassword")

    def test_user_flask_login_properties(self, session):
        """
        Test the properties (`is_active`, `is_authenticated`, `is_anonymous`, `get_id`)
        required by Flask-Login for user session management.
        """
        user = User(email="login@example.com", password="password")
        session.add(user)
        session.commit()

        assert user.is_active is True
        assert user.is_authenticated is True
        assert user.is_anonymous is False
        # get_id should return the user's ID as a string
        assert user.get_id() == str(user.id)

    def test_user_repr(self, session):
        """
        Test the `__repr__` method of the User model to ensure it provides
        a useful string representation for debugging.
        """
        user = User(email="repr@example.com", password="password")
        session.add(user)
        session.commit()
        assert repr(user) == f"<User {user.id}: repr@example.com>"

# --- Test Cases for QRCode Model ---

class TestQRCodeModel:
    """
    Unit tests for the QRCode database model and its methods.
    """

    def test_create_qr_code(self, session):
        """
        Test that a QRCode object can be created and persisted correctly,
        including its foreign key relationship to a User and a default
        `generated_at` timestamp.
        """
        user = User(email="qruser@example.com", password="password")
        session.add(user)
        session.flush()  # Ensures the user object has an ID before QR code creation

        target_url = "https://example.com/my-qr-code"
        image_filename = "qr_code_abc123.png"
        qr_code = QRCode(user_id=user.id, target_url=target_url, image_filename=image_filename)
        session.add(qr_