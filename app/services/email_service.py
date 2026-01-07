import logging
from flask import current_app
from flask_mail import Mail, Message
from smtplib import SMTPException

# Configure logging for this module
logger = logging.getLogger(__name__)

# --- Expected Flask-Mail Configuration ---
# For this service to function, Flask-Mail must be configured in your Flask app's config.
# Example configuration (e.g., in config.py or environment variables):
#
# MAIL_SERVER = 'smtp.mailgun.org' # Or 'smtp.sendgrid.net', 'smtp.gmail.com', etc.
# MAIL_PORT = 587
# MAIL_USE_TLS = True
# MAIL_USE_SSL = False
# MAIL_USERNAME = 'your_smtp_username'
# MAIL_PASSWORD = 'your_smtp_password'
# MAIL_DEFAULT_SENDER = 'QR Code Genius <noreply@qrcodegenius.com>'
# APP_NAME = 'QR Code Genius' # Used for email branding, from project specs
#
# And initialized in your app factory (e.g., app/__init__.py):
# from flask_mail import Mail
# mail = Mail()
# def create_app():
#     # ... app setup ...
#     mail.init_app(app)
#     # ...
#     return app
# -----------------------------------------


def send_password_reset_email(recipient_email: str, reset_link: str) -> bool:
    """Sends a password reset email to the specified recipient.

    This function constructs and dispatches an email containing a unique link
    for the user to reset their password. It leverages Flask-Mail for sending
    and logs any success or failure during the process.

    Args:
        recipient_email: The email address of the user requesting a password reset.
        reset_link: The unique URL for the user to reset their password. This link
                    should typically contain a secure, time-limited token.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    # Retrieve the Flask-Mail instance from the current application context.
    # It's assumed that Flask-Mail has been initialized as an extension.
    mail = current_app.extensions.get('mail')
    if not mail:
        logger.error("Flask-Mail extension not initialized. Cannot send password reset email. "
                     "Please ensure 'mail.init_app(app)' is called during application setup.")
        return False

    # Retrieve sender and application name from Flask configuration for branding.
    # Default values are provided for robustness, but these should be configured.
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'QR Code Genius <noreply@qrcodegenius.com>')
    app_name = current_app.config.get('APP_NAME', 'QR Code Genius')

    subject = f"[{app_name}] Password Reset Request"

    # Construct the HTML body for a richer email experience.
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{app_name} Password Reset</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ background-color: #007bff; padding: 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; text-align: center; }}
            .header h1 {{ margin: 0; color: #ffffff; font-size: 28px; }}
            .content {{ padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 25px; margin: 20px 0; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; }}
            .button:hover {{ background-color: #218838; }}
            .footer {{ margin-top: 30px; padding: 15px 20px; border-top: 1px solid #eee; font-size: 0.9em; color: #777; text-align: center; }}
            p {{ margin-bottom: 15px; }}
            a {{ color: #007bff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{app_name}</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You have requested to reset the password for your {app_name} account.</p>
                <p>Please click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Your Password</a>
                </p>
                <p>If the button above does not work, you can also copy and paste the following link into your browser:</p>
                <p><a href="{reset_link}">{reset_link}</a></p>
                <p>This link is valid for a limited time (e.g., 1 hour) for security reasons. If you did not request a password reset, please ignore this email.</p>
                <p>Thank you,</p>
                <p>The {app_name} Team</p>
            </div>
            <div class="footer">
                <p>&copy; {app_name}. All rights reserved.</p>
                <p>This is an automated email, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Construct the plain text body as a fallback for email clients that don't render HTML.
    text_body = f"""
Hello,

You have requested to reset the password for your {app_name} account.
Please click on the following link to reset your password:
{reset_link}

This link is valid for a limited time (e.g., 1 hour) for security reasons.
If you did not request a password reset, please ignore this email.

Thank you,
The {app_name} Team

---
This is an automated email, please do not reply.
© {app_name}. All rights reserved.
"""

    # Create a new email message.
    msg = Message(subject, sender=sender, recipients=[recipient_email])
    msg.body = text_body  # Set plain text body
    msg.html = html_body  # Set HTML body

    try:
        # Attempt to send the email.
        mail.send(msg)
        logger.info(f"Password reset email successfully sent to {recipient_email}")
        return True
    except SMTPException as e:
        # Catch specific SMTP errors (e.g., connection issues, authentication failures).
        logger.error(f"SMTP error while sending password reset email to {recipient_email}: {e}")
    except Exception as e:
        # Catch any other unexpected errors during email sending.
        logger.error(f"An unexpected error occurred while sending password reset email to {recipient_email}: {e}")
    return False