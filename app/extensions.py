from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Initialize Flask extensions without binding them to an app yet
# This allows for creating the extensions once and then initializing them with the app later,
# which is useful for factory patterns or testing.
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def init_app(app):
    """
    Initializes all Flask extensions with the given Flask application instance.

    Args:
        app (Flask): The Flask application instance.
    """
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'  # Specify the view function for logging in
    login_manager.login_message_category = 'info' # Category for flash messages

    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads a user from the database given their user ID.
        This function is required by Flask-Login.

        Args:
            user_id (str): The ID of the user to load.

        Returns:
            User: The User object if found, otherwise None.
        """
        # Import User model here to avoid circular imports, as models might import db from extensions.
        from app.models.user import User
        return User.query.get(int(user_id))