import os
from datetime import timedelta

# Determine the base directory of the application.
# This assumes config.py is located directly in the project's root directory.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Base configuration class for the QR Code Genius application.
    Contains common settings applicable to all environments (Development, Testing, Production).
    Environment-specific configurations will inherit from this class and override as needed.
    """
    # --- Core Application Settings ---
    APP_NAME = os.environ.get('APP_NAME', 'QR Code Genius')
    # A strong, random secret key is crucial for Flask security (sessions, CSRF protection).
    # In production, this MUST be overridden by an environment variable.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_please_change_this_in_production_for_security_reasons_12345')
    # A separate salt for password hashing, distinct from SECRET_KEY.
    # In production, this MUST be overridden by an environment variable.
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'dev_password_salt_change_this_too_in_production_67890')
    # How long user sessions persist without re-authentication.
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # --- Database Configuration ---
    # Default placeholder URI. Specific environments will provide their own.
    # PostgreSQL is recommended for production scalability and data integrity.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://qrgenius_user:qrgenius_password@localhost:5432/qrgenius_dev')
    # Disable Flask-SQLAlchemy event system for better performance and to suppress warnings.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- QR Code Generation & Storage Settings ---
    # Base path for storing generated QR code images.
    # This path is relative to the project's root directory.
    QR_CODE_STORAGE_PATH = os.path.join(BASE_DIR, 'qr_codes_storage')
    # Default size of each module (pixel) in the QR code.
    QR_CODE_DEFAULT_SIZE = 10
    # Default border size around the QR code (number of modules).
    QR_CODE_DEFAULT_BORDER = 4
    # Default error correction level for QR codes: L (low), M (medium), Q (quartile), H (high).
    QR_CODE_DEFAULT_ERROR_CORRECTION = 'H'
    # Default image format for generated QR codes.
    QR_CODE_DEFAULT_FORMAT = 'PNG'
    # Flag to enable/disable SVG format generation.
    QR_CODE_SVG_FORMAT_ENABLED = True
    # Path for storing SVG format QR codes, if enabled.
    QR_CODE_SVG_STORAGE_PATH = os.path.join(QR_CODE_STORAGE_PATH, 'svg')

    # Ensure the base QR code storage directory exists.
    os.makedirs(QR_CODE_STORAGE_PATH, exist_ok=True)
    # Ensure the SVG specific storage directory exists if SVG generation is enabled.
    if QR_CODE_SVG_FORMAT_ENABLED:
        os.makedirs(QR_CODE_SVG_STORAGE_PATH, exist_ok=True)

    # --- Email Configuration (for password reset, account verification, etc.) ---
    # Mail server host. Example: 'smtp.mailtrap.io' for development, or your actual SMTP server.
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.mailtrap.io')
    # Mail server port. Common ports: 25, 465 (SSL), 587 (TLS).
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 2525))
    # Use TLS (Transport Layer Security) for secure email communication.
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    # Use SSL (Secure Sockets Layer) for secure email communication.
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    # Username for SMTP authentication.
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_mailtrap_username')
    # Password for SMTP authentication.
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_mailtrap_password')
    # Default sender email address for application-generated emails.
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@qr-code-genius.com')

    # --- Logging Configuration ---
    # Path for application log files.
    LOG_FILE_PATH = os.path.join(BASE_DIR, 'logs', 'app.log')
    # Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    # Ensure the log directory exists.
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # --- File Uploads / Content Limits ---
    # Maximum content length for incoming requests (e.g., for future logo uploads).
    # 16 MB is a common default to prevent excessively large requests.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 Megabytes

    @staticmethod
    def init_app(app):
        """
        Initializes the Flask application with configuration settings.
        This method can be extended to perform any setup that requires the Flask app instance
        after configuration has been loaded.
        """
        pass # Currently, no specific app-level setup is needed in the base config.


class DevelopmentConfig(Config):
    """
    Development specific configuration for the QR Code Genius application.
    Inherits from Config and overrides settings for a development environment.
    """
    DEBUG = True # Enable debug mode, providing detailed error pages and auto-reloading.
    TESTING = False # Not a testing environment.
    # Development database URI. Using PostgreSQL for consistency with production setup.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL',
                                             f"postgresql://qrgenius_dev:dev_password@localhost:5432/qrgenius_dev")
    MAIL_DEBUG = True # Enable debug logging for Flask-Mail in development.
    # Separate storage path for development QR codes to avoid cluttering production data.
    QR_CODE_STORAGE_PATH = os.path.join(BASE_DIR, 'qr_codes_storage', 'dev')
    QR_CODE_SVG_STORAGE_PATH = os.path.join(QR_CODE_STORAGE_PATH, 'svg')
    LOG_LEVEL = os.environ.get('DEV_LOG_LEVEL', 'DEBUG').upper() # Verbose logging in development.

    # Ensure development specific QR code storage directories exist.
    os.makedirs(QR_CODE_STORAGE_PATH, exist_ok=True)
    os.makedirs(QR_CODE_SVG_STORAGE_PATH, exist_ok=True)


class TestingConfig(Config):
    """
    Testing specific configuration for the QR Code Genius application.
    Inherits from Config and overrides settings for an automated testing environment.
    """
    TESTING = True # Enable testing mode, which propagates exceptions rather than invoking the error handlers.
    DEBUG = True # Debugging can be useful during tests to see detailed errors.
    # Use an in-memory SQLite database for fast, isolated, and disposable tests.
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False # Disable CSRF protection for easier form submission in tests.
    MAIL_SUPPRESS_SEND = True # Prevent actual emails from being sent during tests.
    # Separate storage path for testing QR codes.
    QR_CODE_STORAGE_PATH = os.path.join(BASE_DIR, 'qr_