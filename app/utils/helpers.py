import os
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional, Any

# --- Configuration Constants ---
# In a full Flask application, these values would typically be loaded from
# `app.config` or a dedicated configuration module. For this standalone
# helper file, we use `os.getenv` as a flexible way to get configuration
# from the environment, with a sensible default.
# Ensure the directory specified by QR_CODE_STORAGE_DIR is created and
# writable by the application process.
QR_CODE_STORAGE_DIR = os.getenv('QR_CODE_STORAGE_DIR', 'qr_codes_storage')


def get_env_variable(key: str, default: Optional[Any] = None) -> Any:
    """
    Retrieves an environment variable by its key.

    This helper provides a consistent way to access environment variables
    throughout the application, allowing for default values if a variable
    is not set.

    Args:
        key (str): The name of the environment variable to retrieve.
        default (Optional[Any]): The default value to return if the
                                 environment variable is not found.

    Returns:
        Any: The value of the environment variable, or the specified default value.
    """
    return os.getenv(key, default)


def validate_url(url: str) -> bool:
    """
    Performs robust validation on a given URL string.

    This function ensures the URL is well-formed, uses a safe scheme (http/https),
    and prevents common malicious inputs like 'javascript:' schemes.
    It checks for:
    1.  Non-empty and string type input.
    2.  Presence of a valid scheme ('http' or 'https').
    3.  Presence of a network location (domain or IP address).
    4.  Basic structural validity of the netloc (domain/IP format).
    5.  Absence of 'javascript:' in path or query components.

    Args:
        url (str): The URL string to validate.

    Returns:
        bool: True if the URL is considered valid and safe, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False

    # Strip leading/trailing whitespace from the URL
    url = url.strip()

    # Prepend 'http://' if no scheme is provided. This helps `urlparse` correctly
    # identify the network location for common cases like 'example.com'.
    # The scheme will be re-validated later.
    if '://' not in url:
        url_with_scheme = 'http://' + url
    else:
        url_with_scheme = url

    try:
        parsed_url = urlparse(url_with_scheme)

        # 1. Validate the scheme: Must be 'http' or 'https'.
        if parsed_url.scheme not in ('http', 'https'):
            return False

        # 2. Validate the network location: Must not be empty.
        if not parsed_url.netloc:
            return False

        # 3. Perform a basic regex check on the network location (domain/IP).
        # This regex broadly covers standard domain names and IPv4 addresses.
        # It's designed to catch obvious malformations but is not exhaustive
        # for all possible valid domain name rules (e.g., internationalized domain names).
        domain_ip_regex = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$"  # Domain names
            r"|^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"  # IPv4 addresses
        )
        if not domain_ip_regex.match(parsed_url.netloc):
            return False

        # 4. Prevent common XSS vectors by checking for 'javascript:' in path or query.
        if 'javascript:' in (parsed_url.path or '').lower() or \
           'javascript:' in (parsed_url.query or '').lower():
            return False

        return True
    except ValueError:
        # `urlparse` can raise a ValueError for extremely malformed URLs.
        return False
    except Exception:
        # Catch any other unexpected errors during URL parsing.
        return False


def generate_unique_filename(user_id: int, extension: str = 'png') -> str:
    """
    Generates a unique filename for a QR code image.

    The filename incorporates a precise timestamp, the user's ID, and a
    truncated UUID (Universally Unique Identifier) to ensure high uniqueness.
    The format is `qr_code_YYYYMMDD_HHMMSS_user<user_id>_<uuid_prefix>.<extension>`.

    Args:
        user_id (int): The ID of the user generating the QR code.
        extension (str): The desired file extension (e.g., 'png', 'svg').

    Returns:
        str: A unique filename string suitable for storage.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Use the first 12 characters of a UUID for strong uniqueness while keeping the filename manageable.
    unique_id_prefix = uuid.uuid4().hex[:12]
    # Sanitize the extension to ensure it's lowercase and doesn't contain path separators.
    clean_extension = extension.lower().replace('/', '').replace('\\', '')
    return f"qr_code_{timestamp}_user{user_id}_{unique_id_prefix}.{clean_extension}"


def get_qr_code_storage_path(filename: str) -> str:
    """
    Constructs the full absolute path to a QR code image file within the designated
    storage directory.

    This function also ensures that the storage directory and any necessary
    intermediate directories exist, creating them if they don't.

    Args:
        filename (str): The filename of the QR code image (e.g., generated by `generate_unique_filename`).

    Returns:
        str: The absolute path to where the QR code file should be stored or is located.
    """
    # Ensure the storage directory exists. `exist_ok=True` prevents an error
    # if the directory already exists. This creates all necessary intermediate directories.
    os.makedirs(QR_CODE_STORAGE_DIR, exist_ok=True)
    return os.path.join(QR_CODE_STORAGE_DIR, filename)


def delete_qr_code_file(filename: str) -> bool:
    """
    Deletes a QR code image file from the application's storage directory.

    This function handles cases where the file might not exist (idempotency)
    and catches potential OS errors during deletion.

    Args:
        filename (str): The filename of the QR code image to delete.

    Returns:
        bool: True if the file was successfully deleted or did not exist, False otherwise
              (e.g., due to permission issues or other OS errors).
    """
    file_path = get_qr_code_storage_path(filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        else:
            # If the file does not exist, consider the operation successful
            # as the desired state (file absent) is achieved.
            return True
    except OSError as e:
        # Log the error for debugging. In a production Flask application,
        # you would typically use `current_app.logger.error` or a more
        # sophisticated logging setup.
        print(f"ERROR: Failed to delete QR code file '{file_path}': {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a string to make it safe for use as a filename.

    This function replaces spaces with underscores and removes characters that
    are typically invalid or problematic across different operating systems.
    It's particularly useful if filenames are derived from user-provided input,
    though in this project, primary filenames are system-generated for security.

    Args:
        filename (str): The original string to sanitize.

    Returns:
        str: The sanitized filename string. Returns an empty string if input is invalid,
             or a UUID if sanitization results in an empty string.
    """
    if not filename or not isinstance(filename, str):
        return ""

    # Replace spaces with underscores
    sanitized = filename.replace(' ', '_')

    # Remove characters that are not alphanumeric, underscore, hyphen, or dot.
    # This regex keeps letters, numbers, underscores, hyphens, and single dots.
    sanitized = re.sub(r'[^\w\-\.]', '', sanitized)

    # Ensure no multiple dots (e.g., "file..name.txt" -> "file.name.txt")
    sanitized = re.sub(r'\.{2,}', '.', sanitized)

    # Remove leading/trailing dots, hyphens, or underscores that might result from sanitization.
    sanitized = sanitized.strip('.-_')

    # If sanitization results in an empty string, generate a UUID as a fallback filename
    if not sanitized:
        return uuid.uuid4().hex

    return sanitized