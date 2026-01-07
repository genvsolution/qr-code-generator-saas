import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

# Initialize Flask extensions globally, but defer initialization with the app
# until the create_app factory function is called.
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=Config):
    """
    Flask application factory function.

    This function initializes the Flask application, loads configuration,
    sets up all necessary extensions (SQLAlchemy, Bcrypt, Flask-Login, Migrate),
    registers blueprints, and configures logging for the application.

    Using the application factory pattern allows for flexible configuration,
    easier testing, and managing multiple instances of the application.

    Args:
        config_class (class): The configuration class to use for the application.
                              Defaults to the production-ready `Config` class.

    Returns:
        Flask: The fully initialized Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the Flask application instance
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configure Flask-Login settings
    login_manager.login_view = 'users.login'  # The endpoint name for the login page
    login_manager.login_message_category = 'info'  # Category for flash messages

    # Import the User model here to avoid circular imports.
    # The models module will import 'db' from this file, so 'User' must be
    # imported after 'db' is initialized and before 'db.create_all()' or similar.
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        """
        Required by Flask-Login. This function reloads the user object from
        the user ID stored in the session.

        Args:
            user_id (str): The ID of the user to load, typically stored as a string.

        Returns:
            User or None: The User object if found, otherwise None.
        """
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Failed to load user with ID '{user_id}': {e}")
            return None

    # Register Blueprints
    # Blueprints organize the application into smaller, reusable components.
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/users')  # Routes prefixed with /users

    from app.qr_codes import bp as qr_codes_bp
    app.register_blueprint(qr_codes_bp, url_prefix='/qr')  # Routes prefixed with /qr

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # Configure Logging for production environments
    if not app.debug and not app.testing:
        if app.config.get('LOG_TO_STDOUT'):
            # Log to standard output (console), useful for containerized environments
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            # Log to a file with rotation
            if not os.path.exists('logs'):
                try:
                    os.mkdir('logs')
                except OSError as e:
                    # Handle potential errors during directory creation
                    app.logger.error(f"Could not create logs directory: {e}")
                    # Fallback to console logging if directory creation fails
                    stream_handler = logging.StreamHandler()
                    stream_handler.setLevel(logging.INFO)
                    app.logger.addHandler(stream_handler)
            else:
                file_handler = RotatingFileHandler(
                    'logs/qr_code_genius.log', maxBytes=10240, backupCount=10
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('QR Code Genius startup')

    return app