from flask import Blueprint, render_template, current_app

# Create a Blueprint for the main public-facing routes of the application.
# This blueprint will handle routes like the homepage, about, contact, and privacy policy.
main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    """
    Renders the homepage of the 'QR Code Genius' application.

    This route serves as the primary landing page for users, providing an overview
    of the service and typically includes calls to action for QR code generation,
    user signup, or login.

    Returns:
        str: The rendered HTML content for the homepage.
    """
    try:
        current_app.logger.info("Accessing the application homepage.")
        return render_template('main/home.html', title='Home - QR Code Genius')
    except Exception as e:
        current_app.logger.error(f"Failed to render homepage: {e}")
        # In a production environment, you might render a custom error page
        # or redirect to a generic error handler.
        return render_template('errors/500.html'), 500 # Assuming an errors blueprint/template exists

@main.route('/about')
def about():
    """
    Renders the 'About Us' page of the application.

    This page provides information about the 'QR Code Genius' platform, its mission,
    features, and potentially the team or technology behind it.

    Returns:
        str: The rendered HTML content for the about page.
    """
    try:
        current_app.logger.info("Accessing the 'About Us' page.")
        return render_template('main/about.html', title='About Us - QR Code Genius')
    except Exception as e:
        current_app.logger.error(f"Failed to render about page: {e}")
        return render_template('errors/500.html'), 500

@main.route('/contact')
def contact():
    """
    Renders the 'Contact Us' page of the application.

    This page typically includes information on how users can get in touch with
    support or the company, such as an email address, a contact form (though form
    submission logic would be in a separate handler), or social media links.

    Returns:
        str: The rendered HTML content for the contact page.
    """
    try:
        current_app.logger.info("Accessing the 'Contact Us' page.")
        return render_template('main/contact.html', title='Contact Us - QR Code Genius')
    except Exception as e:
        current_app.logger.error(f"Failed to render contact page: {e}")
        return render_template('errors/500.html'), 500

@main.route('/privacy')
def privacy():
    """
    Renders the 'Privacy Policy' page of the application.

    This crucial legal page outlines the data collection, usage, storage, and
    protection policies of 'QR Code Genius', ensuring transparency and compliance
    with privacy regulations.

    Returns:
        str: The rendered HTML content for the privacy policy page.
    """
    try:
        current_app.logger.info("Accessing the 'Privacy Policy' page.")
        return render_template('main/privacy.html', title='Privacy Policy - QR Code Genius')
    except Exception as e:
        current_app.logger.error(f"Failed to render privacy policy page: {e}")
        return render_template('errors/500.html'), 500