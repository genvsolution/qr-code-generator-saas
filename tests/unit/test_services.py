import unittest
from unittest import mock
import os
import uuid
from datetime import datetime

# --- Mocking Global Flask Dependencies for Unit Tests ---
# We need to mock Flask's `current_app` and extensions like `db`, `bcrypt`
# as service modules typically import them directly.
# This setup ensures that when service modules are imported, they receive
# these mocked objects instead of real ones, allowing for isolated testing.

# Mock `flask.current_app` and its `config` attribute.
# This needs to be done before importing any service that might access `current_app.config`.
with mock.patch('flask.current_app') as mock_current_app:
    mock_current_app.config = {
        'QR_CODE_STORAGE_PATH': '/tmp/qr_codes',
        'QR_CODE_BASE_URL': 'http://localhost:5000/download_qr/',
        'MAIL_SERVER': 'smtp.example.com',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': 'test@example.com',
        'MAIL_PASSWORD': 'password',
        'MAIL_DEFAULT_SENDER': 'noreply@example.com',
        'PASSWORD_RESET_SECRET': 'super-secret-reset-key', # For password reset token generation/validation
        'REGISTRATION_CONFIRMATION_SECRET': 'super-secret-confirm-