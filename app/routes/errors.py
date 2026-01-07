from flask import Blueprint, render_template, request

# Create a Blueprint for custom error handlers
errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """
    Handles 404 Not Found errors.
    This function is registered globally for the Flask application
    to catch any 404 errors that occur, rendering a custom error page.

    Args:
        error: The exception object associated with the 404 error.

    Returns:
        A tuple containing the rendered HTML template for the 404 page
        and the HTTP status code 404.
    """
    # In a production environment, you might log specific details about the
    # URL that was not found for debugging purposes.
    # For example: current_app.logger.warning(f"404 Not Found for URL: {request.url}")
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_server_error(error):
    """
    Handles 500 Internal Server Error errors.
    This function is registered globally for the Flask application
    to catch any unhandled exceptions, rendering a custom error page.

    Args:
        error: The exception object associated with the 500 error.

    Returns:
        A tuple containing the rendered HTML template for the 500 page
        and the HTTP status code 500.
    """
    # For 500 errors, it's crucial to log the full traceback for debugging.
    # In a real application, you would use current_app.logger.error()
    # and potentially send an alert to developers.
    # Example: current_app.logger.error(f"500 Internal Server Error: {error}", exc_info=True)
    return render_template('errors/500.html'), 500

# Additional error handlers can be added here as needed, e.g., 403 Forbidden, 401 Unauthorized.
# @errors_bp.app_errorhandler(403)
# def forbidden_error(error):
#     """
#     Handles 403 Forbidden errors.
#     Renders a custom 403 error page.
#     """
#     return render_template('errors/403.html'), 403

# @errors_bp.app_errorhandler(401)
# def unauthorized_error(error):
#     """
#     Handles 401 Unauthorized errors.
#     Renders a custom 401 error page.
#     """
#     return render_template('errors/401.html'), 401