import re
from urllib.parse import urlparse, urlunparse
import idna  # For robust Internationalized Domain Name handling
import ipaddress  # For checking if an IP is private

class InvalidURLError(ValueError):
    """Custom exception for invalid URL formats or properties."""
    pass

class URLValidator:
    """
    Provides robust server-side URL validation logic for the QR Code Genius platform.

    Ensures URLs are well-formed, use allowed schemes (HTTP/HTTPS),
    and do not point to potentially malicious or internal resources.
    """

    # Maximum allowed URL length to prevent database bloat and QR code complexity issues.
    # Common browser limits are 2048-8192, 2048 is a safe and widely supported length.
    MAX_URL_LENGTH = 2048

    # Allowed schemes for QR code generation.
    ALLOWED_SCHEMES = {'http', 'https'}

    def __init__(self):
        """
        Initializes the URLValidator.
        No specific state is required for this validator, but the constructor is provided
        for consistency and future extensibility.
        """
        pass

    def _is_private_ip(self, ip_address_str: str) -> bool:
        """
        Checks if an IP address string belongs to a private network range or is a loopback address.
        This method does NOT perform DNS resolution; it only checks the string format
        against known private IP ranges (RFC 1918, RFC 6890) and loopback addresses.

        Args:
            ip_address_str (str): The IP address string to check.

        Returns:
            bool: True if the IP address is private or loopback, False otherwise.
        """
        try:
            ip_obj = ipaddress.ip_address(ip_address_str)
            # is_private covers RFC 1918, RFC 6890 (link-local), etc.
            # is_loopback covers 127.0.0.1 and ::1
            return ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            # Not a valid IP address string, or malformed.
            # Treat as not private if it can't be parsed as an IP.
            return False

    def validate_url(self, url: str) -> str:
        """
        Validates a URL string based on project requirements for QR Code Genius.

        Performs the following robust server-side checks:
        1.  Ensures the URL is not empty, None, or excessively long.
        2.  Parses the URL into its components.
        3.  Handles Internationalized Domain Names (IDN) by converting the hostname
            to its Punycode equivalent (e.g., "bücher.de" -> "xn--bcher-kva.de").
        4.  Validates that the URL uses an allowed scheme (http or https).
        5.  Ensures a valid network location (domain or IP address) is present.
        6.  Prevents URLs from pointing to private IP addresses or loopback addresses
            (a basic form of Server-Side Request Forgery - SSRF - prevention for QR targets).
        7.  Reconstructs and returns a normalized URL string.

        Args:
            url (str): The URL string to validate.

        Returns:
            str: The normalized and validated URL string (e.g., with Punycode hostname,
                 lowercase scheme, and default scheme added if missing).

        Raises:
            InvalidURLError: If the URL fails any validation check, with a descriptive message.
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError("URL cannot be empty and must be a string.")

        # 1. Check URL length
        if len(url) > self.MAX_URL_LENGTH:
            raise InvalidURLError(
                f"URL exceeds maximum allowed length of {self.MAX_URL_LENGTH} characters."
            )

        # Attempt to parse the URL. If no scheme is provided, urlparse might misinterpret
        # the domain as the path or netloc without a scheme.
        parsed_url = urlparse(url)

        # If scheme is missing but it looks like a domain, prepend 'http://' and re-parse.
        # This improves user experience for inputs like "example.com/path".
        if not parsed_url.scheme and parsed_url.netloc and '.' in parsed_url.netloc:
            url = f"http://{url}"
            parsed_url = urlparse(url)
        elif not parsed_url.scheme and not parsed_url.netloc and parsed_url.path:
            # Case like "example.com" without scheme, urlparse puts it in path
            # Try to treat it as a domain and prepend http://
            if '.' in parsed_url.path:
                url = f"http://{parsed_url.path}"
                parsed_url = urlparse(url)

        # Re-check if parsing was successful after potential scheme addition
        if not parsed_url.scheme or not parsed_url.netloc:
            raise InvalidURLError("URL is malformed or missing a valid scheme and domain/IP.")

        # 2. Validate scheme
        if parsed_url.scheme.lower() not in self.ALLOWED_SCHEMES:
            raise InvalidURLError(
                f"Invalid URL scheme '{parsed_url.scheme}'. Only {', '.join(self.ALLOWED_SCHEMES)} are allowed."
            )

        # 3. Validate network location (netloc/hostname)
        if not parsed_url.hostname:  # hostname is netloc without port
             raise InvalidURLError("URL is missing a hostname (domain or IP address).")

        # Handle Internationalized Domain Names (IDN) by converting to Punycode.
        # This ensures consistency and compatibility with various systems.
        try:
            # idna.encode returns bytes, we need string for urlunparse.
            # uts46=True applies Unicode Technical Standard #46 for better normalization.
            punycode_hostname = idna.encode(parsed_url.hostname, uts46=True).decode('ascii')
            if punycode_hostname != parsed_url.hostname:
                # Reconstruct netloc carefully, preserving port if present.
                new_netloc = punycode_hostname
                if parsed_url.port:
                    new_netloc = f"{punycode_hostname}:{parsed_url.port}"
                
                # Update the parsed_url tuple with the new netloc
                parsed_url = parsed_url._replace(netloc=new_netloc)
        except idna.IDNAError as e:
            raise InvalidURLError(f"Invalid Internationalized Domain Name (IDN): {e}")
        except Exception as e:
            # Catch any other unexpected errors during IDN processing
            raise InvalidURLError(f"Error processing hostname: {e}")

        # 4. Basic SSRF prevention: Check if hostname is a private IP or loopback.
        # We use the potentially punycode-converted hostname for this check.
        if self._is_private_ip(parsed_url.hostname):
            raise InvalidURLError(
                f"URL points to a private or loopback IP address ({parsed_url.hostname}), which is not allowed."
            )
        
        # 5. Reconstruct the URL to ensure it's in a canonical form (e.g., with default port removed,
        # scheme lowercase, punycode applied).
        # urlunparse expects a tuple of 6 elements: (scheme, netloc, path, params, query, fragment).
        # Ensure scheme is lowercase for consistency.
        normalized_url = urlunparse(parsed_url._replace(scheme=parsed_url.scheme.lower()))

        # Final check for empty or invalid characters after normalization.
        if not normalized_url:
            raise InvalidURLError("Normalized URL is empty or invalid after processing.")

        return normalized_url

# Example usage (for testing purposes, not part of the service class itself):
if __name__ == '__main__':
    validator = URLValidator()

    test_urls = {
        "Valid HTTP": "http://www.example.com/path?query=1#fragment",
        "Valid HTTPS": "https://sub.domain.co.uk/another/path",
        "Valid with IDN": "https://bücher.example.com",
        "Valid with IP": "http://1.1.1.1/resource",
        "Valid without scheme (auto-corrected)": "www.google.com/search?q=qr",
        "Valid without scheme (auto-corrected, simple)": "example.com",
        "Valid with port": "http://example.com:8080/app",
        "Invalid Scheme (FTP)": "ftp://fileserver.com/data",
        "Invalid Scheme (Javascript)": "javascript:alert('XSS')",
        "Invalid Scheme (File)": "file:///etc/passwd",
        "Invalid Private IP": "http://192.168.1.1/admin",
        "Invalid Loopback IP": "http://127.0.0.1/dashboard",
        "Invalid Loopback IPv6": "https://[::1]/status",
        "Invalid Localhost": "http://localhost/test",
        "Invalid Malformed": "http://.com",
        "Invalid Empty": "",
        "Invalid None": None,
        "Invalid Too Long": "http://example.com/" + "a" * 2040, # Exceeds 2048 total
        "Invalid Bad IDN": "https://xn--bcher-kva.com\x00", # Null byte injection attempt
        "Invalid No Hostname": "http:///path",
        "Invalid No Hostname (just path)": "/some/path",
        "Invalid No Hostname (just query)": "?q=test",
    }

    print("--- URL Validation Tests ---")
    for name, url in test_urls.items():
        print(f"\nTesting: {name} ({url})")
        try:
            validated_url = validator.validate_url(url)
            print(f"  SUCCESS: {validated_url}")
        except InvalidURLError as e:
            print(f"  FAILED: {e}")
        except Exception as e:
            print(f"  UNEXPECTED ERROR: {e}")