from flask import Blueprint, request, jsonify, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import re # For email validation

# Assuming these are initialized in app/__init__.py or app/extensions.py
# and that User model is defined in app/models.py
from app.extensions import db, bcrypt, login_manager
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@login_manager.user_loader
def load_user(user_id):
    """
    Loads a user from the database given their ID.
    Required by Flask-Login to retrieve a user from the session.
    """
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        current_app.logger.error(f"Error loading user with ID {user_id}: {e}")
        return None

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Handles user registration.
    Expects JSON input with 'email' and 'password'.
    Hashes the password and creates a new user in the database.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    # Basic email format validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': 'Invalid email format.'}), 400

    # Password strength validation (example: min 8 characters)
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long.'}), 400

    try:
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'User with this email already exists.'}), 409 # Conflict

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Registration successful. Please log in.'}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during registration for email {email}: {e}")
        return jsonify({'error': 'An unexpected error occurred during registration. Please try again later.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login.
    Expects JSON input with 'email' and 'password'.
    Verifies credentials and logs in the user using Flask-Login.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    try:
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return jsonify({'message': 'Login successful.', 'user_id': user.id, 'email': user.email}), 200
        else:
            return jsonify({'error': 'Invalid email or password.'}), 401

    except Exception as e:
        current_app.logger.error(f"Error during login for email {email}: {e}")
        return jsonify({'error': 'An unexpected error occurred during login. Please try again later.'}), 500

@auth_bp.route('/logout', methods=['POST']) # Using POST for logout as it's a state-changing operation
@login_required
def logout():
    """
    Handles user logout.
    Requires the user to be logged in.
    Logs out the current user using Flask-Login.
    """
    try:
        logout_user()
        return jsonify({'message': 'Logout successful.'}), 200
    except Exception as e:
        current_app.logger.error(f"Error during logout for user {current_user.id if current_user.is_authenticated else 'anonymous'}: {e}")
        return jsonify({'error': 'An unexpected error occurred during logout. Please try again later.'}), 500

@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    """
    Initiates the password reset process.
    Expects JSON input with 'email'.
    Sends a password reset link to the user's email if the account exists.
    """
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required.'}), 400

    try:
        user = User.query.filter_by(email=email).first()

        # Always return a generic success message to prevent email enumeration
        if user:
            # Generate a secure, timed token
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            # Using user.id as payload, with a specific salt for password resets
            token = s.dumps(user.id, salt='password-reset-salt')

            # Construct the reset URL (frontend would typically handle this or redirect)
            # For an API, we'd typically return the token or a confirmation,
            # and the frontend would construct the full URL.
            # Here, we'll simulate sending an email with the link.
            reset_link = url_for('auth.reset_password', token=token, _external=True)

            # In a real application, send this email using a mail service
            # Example: mail.send_message(subject="Password Reset Request",
            #                           recipients=[user.email],
            #                           body=f"Click the following link to reset your password: {reset_link}")
            current_app.logger.info(f"Password reset link generated for {user.email}: {reset_link}")
            # For now, just log it.

        return jsonify({'message': 'If an account with that email exists, a password reset link has been sent to your inbox.'}), 200

    except Exception as e:
        current_app.logger.error(f"Error during forgot password request for {email}: {e}")
        return jsonify({'error': 'An unexpected error occurred while processing your request. Please try again later.'}), 500

@auth_bp.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    """
    Resets the user's password using a valid token.
    Expects JSON input with 'new_password'.
    """
    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({'error': 'New password is required.'}), 400

    # Password strength validation (example: min 8 characters)
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters long.'}), 400

    try:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        user_id = None
        try:
            # Load the user ID from the token, valid for 1 hour (3600 seconds)
            user_id = s.loads(token, salt='password-reset-salt', max_age=3600)
        except SignatureExpired:
            return jsonify({'error': 'The password reset link has expired.'}), 400
        except BadTimeSignature:
            return jsonify({'error': 'The password reset link is invalid or malformed.'}), 400

        user = User.query.get(user_id)

        if not user:
            # This case should ideally not happen if token is valid, but good for robustness
            return jsonify({'error': 'User not found for the provided token.'}), 404

        # Update password
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        return jsonify({'message': 'Your password has been reset successfully. You can now log in with your new password.'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during password reset for token {token}: {e}")
        return jsonify({'error': 'An unexpected error occurred during password reset. Please try again later.'}), 500